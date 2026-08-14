from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.config import settings
from app.services.analytics_service import AnalyticsService
from app.services.search_service import SearchService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def view_dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    """Render Analytics Dashboard page with SQL metrics and Chart.js datasets."""
    metrics = AnalyticsService.get_dashboard_metrics(db)
    chart_data = AnalyticsService.get_chart_data(db)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "app_name": settings.APP_NAME,
            "metrics": metrics,
            "chart_data": chart_data
        }
    )


@router.get("/search", response_class=HTMLResponse)
async def view_global_search(
    request: Request,
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Render unified Global Search page with categorized ticket and KB results."""
    query_str = q.strip() if q else ""
    ticket_results, kb_results = SearchService.global_search(db, query_str) if query_str else ([], [])

    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={
            "app_name": settings.APP_NAME,
            "search_query": query_str,
            "ticket_results": ticket_results,
            "kb_results": kb_results,
            "total_matches": len(ticket_results) + len(kb_results)
        }
    )


@router.get("/api/dashboard/stats")
async def api_dashboard_stats(db: Session = Depends(get_db)):
    """REST API endpoint returning JSON metrics for dashboard charts."""
    metrics = AnalyticsService.get_dashboard_metrics(db)
    chart_data = AnalyticsService.get_chart_data(db)
    return {
        "metrics": metrics,
        "chart_data": chart_data
    }
