import logging
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import ValidationError

from app.database import get_db
from app.config import settings
from app.services.ticket_service import TicketService
from app.schemas import TicketCreate, TicketUpdate, TicketRead

logger = logging.getLogger("service_desk.router.tickets")
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

VALID_STATUSES = ["Open", "In Progress", "Resolved", "Closed"]
VALID_PRIORITIES = ["Low", "Medium", "High", "Urgent"]


# ==========================================
# Web HTML Routes
# ==========================================

@router.get("/tickets", response_class=HTMLResponse)
async def list_tickets(
    request: Request,
    q: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    category_filter: Optional[str] = Query(None, alias="category"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    created: Optional[bool] = False,
    deleted: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    """Render tickets list dashboard by fetching incidents directly from SQLite database."""
    skip = (page - 1) * page_size
    tickets, total_count = TicketService.get_all_tickets(
        db=db,
        query=q,
        status=status_filter,
        priority=priority_filter,
        category=category_filter,
        skip=skip,
        limit=page_size
    )

    categories = TicketService.get_categories(db)
    counts = TicketService.get_ticket_counts(db)
    total_pages = max(1, (total_count + page_size - 1) // page_size)

    return templates.TemplateResponse(
        request=request,
        name="tickets/list.html",
        context={
            "app_name": settings.APP_NAME,
            "tickets": tickets,
            "counts": counts,
            "categories": categories,
            "statuses": VALID_STATUSES,
            "priorities": VALID_PRIORITIES,
            "search_query": q or "",
            "selected_status": status_filter or "All",
            "selected_priority": priority_filter or "All",
            "selected_category": category_filter or "All",
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "created_success": created,
            "deleted_success": deleted
        }
    )


@router.get("/tickets/new", response_class=HTMLResponse)
async def create_ticket_form(
    request: Request,
    db: Session = Depends(get_db)
):
    """Render form to submit a new support ticket."""
    categories = TicketService.get_categories(db)
    return templates.TemplateResponse(
        request=request,
        name="tickets/create.html",
        context={
            "app_name": settings.APP_NAME,
            "categories": categories,
            "priorities": VALID_PRIORITIES,
            "form_data": {},
            "errors": None
        }
    )


@router.post("/tickets")
async def create_ticket_action(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    priority: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process ticket submission with Pydantic validation, SQLite persistence, and database commit."""
    raw_data = {
        "title": title.strip() if title else "",
        "description": description.strip() if description else "",
        "category": category.strip() if category else "General IT",
        "priority": priority.strip() if priority else "Medium"
    }

    try:
        ticket_in = TicketCreate(**raw_data)
        logger.info(f"Processing new ticket submission: Title = '{ticket_in.title}'")
        
        ticket = TicketService.create_ticket(db, ticket_in)
        logger.info(f"Ticket ID #{ticket.id} successfully created and committed to database.")
        
        return RedirectResponse(
            url=f"/tickets/{ticket.id}?created=true",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except ValidationError as e:
        logger.warning(f"Validation failed for ticket creation: {e.errors()}")
        error_msgs = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
        categories = TicketService.get_categories(db)
        return templates.TemplateResponse(
            request=request,
            name="tickets/create.html",
            context={
                "app_name": settings.APP_NAME,
                "categories": categories,
                "priorities": VALID_PRIORITIES,
                "form_data": raw_data,
                "errors": error_msgs
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


@router.get("/tickets/{ticket_id}", response_class=HTMLResponse)
async def view_ticket_detail(
    request: Request,
    ticket_id: int,
    created: Optional[bool] = False,
    updated: Optional[bool] = False,
    resolved: Optional[bool] = False,
    note_added: Optional[bool] = False,
    db: Session = Depends(get_db)
):
    """Render Ticket Detail view fetching directly from database."""
    ticket = TicketService.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Support Ticket #{ticket_id} not found")

    categories = TicketService.get_categories(db)

    return templates.TemplateResponse(
        request=request,
        name="tickets/detail.html",
        context={
            "app_name": settings.APP_NAME,
            "ticket": ticket,
            "categories": categories,
            "statuses": VALID_STATUSES,
            "priorities": VALID_PRIORITIES,
            "created": created,
            "updated": updated,
            "resolved": resolved,
            "note_added": note_added
        }
    )


@router.get("/tickets/{ticket_id}/edit", response_class=HTMLResponse)
async def edit_ticket_form(
    request: Request,
    ticket_id: int,
    db: Session = Depends(get_db)
):
    """Render edit form for a ticket."""
    ticket = TicketService.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_id} not found")

    categories = TicketService.get_categories(db)

    return templates.TemplateResponse(
        request=request,
        name="tickets/edit.html",
        context={
            "app_name": settings.APP_NAME,
            "ticket": ticket,
            "categories": categories,
            "statuses": VALID_STATUSES,
            "priorities": VALID_PRIORITIES,
            "errors": None
        }
    )


@router.post("/tickets/{ticket_id}/edit")
async def update_ticket_action(
    request: Request,
    ticket_id: int,
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    priority: str = Form(...),
    status_val: str = Form(..., alias="status"),
    db: Session = Depends(get_db)
):
    """Process ticket edit submission."""
    ticket = TicketService.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_id} not found")

    raw_data = {
        "title": title.strip(),
        "description": description.strip(),
        "category": category.strip(),
        "priority": priority.strip(),
        "status": status_val.strip()
    }

    try:
        ticket_update = TicketUpdate(**raw_data)
        TicketService.update_ticket(db, ticket_id, ticket_update)
        return RedirectResponse(
            url=f"/tickets/{ticket_id}?updated=true",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except ValidationError as e:
        error_msgs = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
        categories = TicketService.get_categories(db)
        return templates.TemplateResponse(
            request=request,
            name="tickets/edit.html",
            context={
                "app_name": settings.APP_NAME,
                "ticket": ticket,
                "categories": categories,
                "statuses": VALID_STATUSES,
                "priorities": VALID_PRIORITIES,
                "errors": error_msgs
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


@router.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket_action(
    ticket_id: int,
    resolution_notes: str = Form(...),
    db: Session = Depends(get_db)
):
    """Record ticket resolution notes and mark status as Resolved."""
    ticket = TicketService.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_id} not found")

    if not resolution_notes or not resolution_notes.strip():
        raise HTTPException(status_code=400, detail="Resolution notes cannot be empty")

    TicketService.resolve_ticket(db, ticket_id, resolution_notes)
    return RedirectResponse(
        url=f"/tickets/{ticket_id}?resolved=true",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/tickets/{ticket_id}/note")
async def add_ticket_note_action(
    ticket_id: int,
    note_text: str = Form(...),
    db: Session = Depends(get_db)
):
    """Add an internal support note to the ticket timeline."""
    ticket = TicketService.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_id} not found")

    if not note_text or not note_text.strip():
        raise HTTPException(status_code=400, detail="Note text cannot be empty")

    TicketService.add_internal_note(db, ticket_id, note_text)
    return RedirectResponse(
        url=f"/tickets/{ticket_id}?note_added=true",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/tickets/{ticket_id}/delete")
async def delete_ticket_action(
    ticket_id: int,
    db: Session = Depends(get_db)
):
    """Delete ticket from database and redirect to tickets list."""
    success = TicketService.delete_ticket(db, ticket_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_id} not found")

    return RedirectResponse(
        url="/tickets?deleted=true",
        status_code=status.HTTP_303_SEE_OTHER
    )


# ==========================================
# REST API Endpoints (For AJAX Client)
# ==========================================

@router.get("/api/tickets", response_model=List[TicketRead])
async def api_get_tickets(
    q: Optional[str] = None,
    status_val: Optional[str] = Query(None, alias="status"),
    priority_val: Optional[str] = Query(None, alias="priority"),
    category_val: Optional[str] = Query(None, alias="category"),
    db: Session = Depends(get_db)
):
    """REST API endpoint returning JSON list of tickets directly from database."""
    tickets, _ = TicketService.get_all_tickets(
        db, query=q, status=status_val, priority=priority_val, category=category_val
    )
    return tickets


@router.get("/api/tickets/{ticket_id}", response_model=TicketRead)
async def api_get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """REST API endpoint returning a single ticket JSON directly from database."""
    ticket = TicketService.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket
