import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import engine, Base, get_db
from app.routers import kb

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("service_desk")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler to initialize database schema on startup."""
    logger.info("Initializing database tables...")
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
app.include_router(kb.router)


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
    """Root landing page rendering the base enterprise layout."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.APP_NAME
        }
    )


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint verifying application liveness and database connection."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Health check DB connection failed: {e}")
        db_status = "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "app_name": settings.APP_NAME,
        "database": db_status
    }
