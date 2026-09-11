"""Enterprise Local AI Assistant - Main Application Entrypoint."""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.departments import router as departments_router
from app.api.v1.documents import router as documents_router
from app.api.v1.chat import router as chat_router
from app.api.v1.tickets import router as tickets_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.auto_import import router as auto_import_router
from app.api.v1.it_support import router as it_support_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to ensure database and seed data are ready on startup."""
    try:
        from app.db.init_db import init_db
        init_db()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Startup database initialization notice: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Local AI Assistant Backend API with Local LLM (Ollama) & ChromaDB RAG",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(departments_router, prefix=f"{settings.API_V1_STR}/departments", tags=["Departments"])
app.include_router(documents_router, prefix=f"{settings.API_V1_STR}/documents", tags=["Documents"])
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat & AI Assistant"])
app.include_router(tickets_router, prefix=f"{settings.API_V1_STR}/tickets", tags=["IT Tickets & Helpdesk"])
app.include_router(dashboard_router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["Admin Dashboard"])
app.include_router(auto_import_router, prefix=f"{settings.API_V1_STR}/auto-import", tags=["Auto-Import & Watcher"])
app.include_router(it_support_router, prefix=f"{settings.API_V1_STR}/it-support", tags=["IT Support & Network Helpdesk"])


@app.get("/", tags=["General"])
async def root_redirect():
    """Root endpoint welcoming clients and directing to API docs."""
    return {
        "success": True,
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs",
    }


@app.get("/api/health", tags=["Monitoring"], status_code=status.HTTP_200_OK)
@app.get(f"{settings.API_V1_STR}/health", tags=["Monitoring"], status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint to verify backend service readiness."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "status": "healthy",
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "timestamp": time.time(),
            "local_ai": {
                "runtime": "Ollama",
                "llm_model": settings.OLLAMA_LLM_MODEL,
                "embed_model": settings.OLLAMA_EMBED_MODEL,
            }
        }
    )
