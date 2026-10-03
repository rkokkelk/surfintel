from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.router import api_router
from app.db.session import SessionLocal
from app.core import logging
from app.core.config import settings

app = FastAPI(title="SurfIntel API", version="0.1.0")

class CatchAllMiddleware(BaseHTTPMiddleware):
    """An exception handler registered for the bare `Exception` type is
    installed on Starlette's ServerErrorMiddleware, which sits OUTSIDE
    CORSMiddleware — so its response never gets CORS headers, and the browser
    reports a misleading "CORS error" for what's actually a 500 (this is
    exactly what happened with the malformed-enrichment-row crash on
    /items). Catching it here instead, in an `add_middleware` call placed
    BEFORE CORSMiddleware's (which nests it *inside* CORS — verified: an
    unhandled exception here still comes back with
    Access-Control-Allow-Origin set), keeps the real error visible in the
    browser instead of masquerading as a CORS problem.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            logger.exception("Unhandled error on %s %s", request.method, request.url.path)
            return JSONResponse(status_code=500, content={"detail": "Interne serverfout"})


app.add_middleware(CatchAllMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def log_validation_errors(request: Request, exc: RequestValidationError) -> JSONResponse:
    """FastAPI's default 422 body already lists what failed (see `exc.errors()`)
    — this just also puts it in the server log, since that's easy to miss in
    a browser Network tab while a request is failing silently client-side.
    """
    logger.warning("422 on %s %s: %s", request.method, request.url.path, exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


with SessionLocal() as db:
    logging.setup_log_sources(db)
app.include_router(api_router)
