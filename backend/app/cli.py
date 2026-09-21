"""Operational CLI. Run inside the backend container/venv:

    python -m app.cli run-ingestion
    python -m app.cli create-platform-admin --email a@surf.nl --name "Roy" --password ...
    python -m app.cli add-source --name "Security.NL" --feed-url https://www.security.nl/rss/headlines.xml
"""

import typer
import logging
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.ingestion.pipeline import run_ingestion_cycle
from app.models.organization import Organization
from app.models.source import Source, SourceType
from app.models.user import AppUser, UserRole
from app.models.item import Item
from app.ingestion.playwright import PlaywrightBackend

cli = typer.Typer()

logging.basicConfig(level=logging.DEBUG)



@cli.command()
def run_ingestion(force: bool = False) -> None:
    """One ingestion cycle: poll sources, fetch/enrich new items, evaluate alerts."""
    db = SessionLocal()
    fetch_backend = PlaywrightBackend()

    try:
        run_ingestion_cycle(db, fetch_backend, force)
    finally:
        db.close()


@cli.command()
def create_platform_admin(
    email: str = typer.Option(...),
    name: str = typer.Option(...),
    password: str = typer.Option(...),
) -> None:
    """Bootstrap the first super-admin, under a SURF "platform operator" org
    created on demand (see docs/architecture.md — super-admins are just
    app_users of that org with is_platform_admin=True).
    """
    db = SessionLocal()
    try:
        org = db.query(Organization).filter_by(is_platform_operator=True).first()
        if org is None:
            org = Organization(name="SURF", slug="surf", is_platform_operator=True)
            db.add(org)
            db.flush()

        user = AppUser(
            organization_id=org.id,
            email=email,
            name=name,
            role=UserRole.admin,
            is_platform_admin=True,
            password_hash=hash_password(password),
        )
        db.add(user)
        db.commit()
        typer.echo(f"Platform admin '{email}' aangemaakt onder organisatie '{org.slug}'.")
    finally:
        db.close()


@cli.command()
def add_source(
    name: str = typer.Option(...),
    feed_url: str = typer.Option(..., help="RSS/Atom feed URL"),
    poll_interval_seconds: int = typer.Option(3600, help="How often the ingestion cycle should re-poll this feed"),
) -> None:
    """Register an RSS source. Sources are global/shared (see docs/architecture.md
    — one item feed for every organization), so there is no organization_id here.
    `custom_module` sources have no registered connector yet, so this only
    supports `rss`.
    """
    db = SessionLocal()
    try:
        existing = db.scalar(select(Source).where(Source.name == name))
        if existing:
            typer.echo(f"Source '{name}' bestaat al (id={existing.id}) — niets aangemaakt.")
            return

        source = Source(
            name=name,
            type=SourceType.rss,
            config={"feed_url": feed_url},
            poll_interval_seconds=poll_interval_seconds,
        )
        db.add(source)
        db.commit()
        typer.echo(f"Source '{name}' aangemaakt (id={source.id}).")
    finally:
        db.close()


if __name__ == "__main__":
    cli()
