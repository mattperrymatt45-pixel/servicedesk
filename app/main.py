import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import engine, Base, get_db
from app.models import Ticket, KBArticle
from app.services.ai_service import AIService
from app.routers import kb, tickets, ai, dashboard

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("service_desk")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler to initialize database schema on startup."""
    logger.info("Initializing application database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Application startup completed successfully.")
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Mount Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configure Jinja2 Templates
templates = Jinja2Templates(directory="app/templates")

# Register Routers
app.include_router(dashboard.router)
app.include_router(tickets.router)
app.include_router(kb.router)
app.include_router(ai.router)


# ==========================================
# Exception Handlers
# ==========================================
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP Exception {exc.status_code} at {request.url.path}: {exc.detail}")
    
    # Return JSON for API routes
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "status_code": exc.status_code}
        )
    
    # Render template for web HTML routes
    if exc.status_code == 404:
        return templates.TemplateResponse(
            request=request,
            name="404.html",
            context={"app_name": settings.APP_NAME},
            status_code=404
        )
    elif exc.status_code == 500:
        return templates.TemplateResponse(
            request=request,
            name="500.html",
            context={"app_name": settings.APP_NAME},
            status_code=500
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception at {request.url.path}: {str(exc)}", exc_info=True)
    
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "status_code": 500}
        )
        
    return templates.TemplateResponse(
        request=request,
        name="500.html",
        context={"app_name": settings.APP_NAME},
        status_code=500
    )


# ==========================================
# Core Endpoints
# ==========================================
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root landing page redirects directly to the main Support Tickets Dashboard."""
    return RedirectResponse(url="/tickets", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint verifying liveness, DB connection,
    AI client configuration, and record counts.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Health check DB connection failed: {e}")
        db_status = "disconnected"

    # Check AI Service Client
    ai_available = "available" if AIService._get_client() is not None else "unavailable"

    # Fetch Record Counts
    try:
        kb_count = db.query(KBArticle).count()
        ticket_count = db.query(Ticket).count()
    except Exception:
        kb_count = 0
        ticket_count = 0

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "ai_service": ai_available,
        "knowledge_base_articles": kb_count,
        "tickets": ticket_count,
        "app_name": settings.APP_NAME
    }
