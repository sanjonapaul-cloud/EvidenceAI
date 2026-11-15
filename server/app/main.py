"""EvidenceAI backend entry point (Member 2).

Run from the `server` folder:
    uvicorn app.main:app --reload --port 8000
"""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.dependencies import get_settings
from app.core.errors import EvidenceAIError
from app.routes import chat, documents, evaluation, health

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("evidenceai")


def create_app() -> FastAPI:
    settings = get_settings()
    settings.ensure_dirs()

    app = FastAPI(
        title="EvidenceAI API",
        description="Research assistant with verifiable answers (student prototype).",
        version="0.1.0",
    )

    # Allow the React dev server (a different origin) to call this API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(EvidenceAIError)
    async def handle_known_error(_: Request, exc: EvidenceAIError) -> JSONResponse:
        # Messages on these exceptions are written to be safe to show to users.
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error")  # details stay in the server log
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})

    for module in (health, documents, chat, evaluation):
        app.include_router(module.router, prefix="/api")

    if not settings.llm_configured:
        logger.warning(
            "GEMINI_API_KEY is not set. The app will run in retrieval-only mode "
            "(evidence is shown, but no AI answer is generated)."
        )
    return app


app = create_app()
