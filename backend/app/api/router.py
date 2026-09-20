from fastapi import APIRouter

from app.api.routes import alerts, auth, health, items, organizations, sources, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(users.router)
api_router.include_router(sources.router)
api_router.include_router(items.router)
api_router.include_router(alerts.router)
