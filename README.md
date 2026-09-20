# SurfIntel

Open cyber threat intelligence platform voor SURF en aangesloten
onderwijs- en onderzoeksinstellingen. Aggregeert security-nieuws,
vendor-advisories en CERT-bulletins, verrijkt ze automatisch
(CVE/CPE/KEV/categorisatie) en laat instellingen daarop alerts
abonneren via mail/Slack/Teams/webhook (Apprise).

Zie [docs/architecture.md](docs/architecture.md) voor het volledige
ontwerp (stack, datamodel, ingestion-/enrichment-/alerting-pipeline).

## Draaien met Docker

```bash
cp .env.example .env   # vul JWT_SECRET en ENCRYPTION_KEY in
docker compose up --build
```

- Backend: http://localhost:8000/docs (OpenAPI)
- Frontend: http://localhost:3000

De backend draait bij het opstarten automatisch de Alembic-migraties.
Maak daarna de eerste platformbeheerder aan:

```bash
docker compose exec backend python -m app.cli create-platform-admin \
  --email jij@surf.nl --name "Jouw naam" --password kies-een-wachtwoord
```

Log daarmee in via de frontend, maak een organisatie aan
(`POST /organizations`) en een gebruiker binnen die organisatie
(`POST /users`, als admin van die organisatie).

Ingestion (bronnen pollen, items ophalen/verrijken, alerts evalueren)
draait niet automatisch — plan dit bv. via cron of een simpele loop:

```bash
docker compose exec backend python -m app.cli run-ingestion
```

## Lokaal ontwikkelen zonder Docker

**Backend** (Python 3.12+):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head          # vereist een lokale Postgres, zie DATABASE_URL in app/core/config.py
uvicorn app.main:app --reload
pytest                        # unit tests voor CVE-extractie en alert-matching
```

**Frontend** (Node 20+):

```bash
cd frontend
npm install
npm run dev
```

## Status

Dit is een eerste werkende scaffold: auth (lokaal wachtwoord, SSO via
SURFconext later), multi-tenant rollen, de ingestion-/enrichment-pipeline
(RSS-bronnen, CVE/CPE-extractie, CISA KEV-check, een heuristische
categorisatie als eerste versie vooruitlopend op een echte AI-classifier),
en de alerting-engine met Apprise-notificaties zijn end-to-end getest.
Nog niet gebouwd: een `custom_module`-source-implementatie (bv. op basis
van changedetection.io), de CVE/actor-correlatiegraaf, en de
SURFconext SAML2-auth-provider.
