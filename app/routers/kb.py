from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.config import settings
from app.templates_config import templates
from app.services.kb_service import KBService
from app.schemas import KBArticleCreate, KBArticleRead

router = APIRouter()


# ==========================================
# Web HTML Routes
# ==========================================
@router.get("/kb", response_class=HTMLResponse)
async def list_kb_articles(
    request: Request,
    q: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Render Knowledge Base article list page with optional search and category filters."""
    articles = KBService.search_articles(db, query=q, category=category)
    categories = KBService.get_categories(db)

    return templates.TemplateResponse(
        request=request,
        name="kb/list.html",
        context={
            "app_name": settings.APP_NAME,
            "articles": articles,
            "categories": categories,
            "selected_category": category or "All",
            "search_query": q or "",
            "total_count": len(articles)
        }
    )


@router.get("/kb/new", response_class=HTMLResponse)
async def create_kb_article_form(
    request: Request,
    db: Session = Depends(get_db)
):
    """Render form to create a new Knowledge Base article."""
    categories = KBService.get_categories(db)
    return templates.TemplateResponse(
        request=request,
        name="kb/create.html",
        context={
            "app_name": settings.APP_NAME,
            "categories": categories
        }
    )


@router.post("/kb/new")
async def create_kb_article_action(
    title: str = Form(...),
    category: str = Form(...),
    problem: str = Form(...),
    solution: str = Form(...),
    keywords: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Process form submission to create a new Knowledge Base article."""
    article_in = KBArticleCreate(
        title=title,
        category=category,
        problem=problem,
        solution=solution,
        keywords=keywords
    )
    article = KBService.create_article(db, article_in)
    return RedirectResponse(url=f"/kb/{article.id}?created=true", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/kb/{article_id}", response_class=HTMLResponse)
async def view_kb_article(
    request: Request,
    article_id: int,
    created: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    """Render detail view for a specific Knowledge Base article."""
    article = KBService.get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail=f"Knowledge Base article #{article_id} not found")

    return templates.TemplateResponse(
        request=request,
        name="kb/detail.html",
        context={
            "app_name": settings.APP_NAME,
            "article": article,
            "created": created
        }
    )


# ==========================================
# REST API Endpoints (For AJAX & AI Service)
# ==========================================
@router.get("/api/kb", response_model=List[KBArticleRead])
async def api_list_kb_articles(
    q: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """REST API endpoint returning KB articles as JSON."""
    articles = KBService.search_articles(db, query=q, category=category)
    return articles


@router.get("/api/kb/{article_id}", response_model=KBArticleRead)
async def api_get_kb_article(
    article_id: int,
    db: Session = Depends(get_db)
):
    """REST API endpoint returning a single KB article as JSON."""
    article = KBService.get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="KB Article not found")
    return article
