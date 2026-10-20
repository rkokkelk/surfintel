from fastapi import APIRouter, Request

from app.core.config import settings

router = APIRouter(tags=["health"])

@router.get("/version")
def version(request: Request) -> dict:
    return {"version": request.app.version, "commit": settings.commit}

@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
