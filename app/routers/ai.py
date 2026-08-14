from fastapi import APIRouter, Depends, Request, HTTPException, status, Form
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.ticket_service import TicketService
from app.services.kb_service import KBService
from app.services.ai_service import AIService
from app.models import TicketActivity
from datetime import datetime, timezone

router = APIRouter()


@router.post("/tickets/{ticket_id}/triage")
async def trigger_ai_triage_web(
    ticket_id: int,
    db: Session = Depends(get_db)
):
    """Web action to trigger Groq AI triage analysis for a support ticket."""
    ticket = TicketService.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_id} not found")

    # 1. Retrieve 3-5 best matching KB articles
    kb_articles = KBService.search_articles(db, query=ticket.title, category=ticket.category)[:5]
    if not kb_articles:
        kb_articles = KBService.get_all_articles(db, limit=5)

    # 2. Call AI Service
    ai_result = AIService.analyze_ticket(ticket, kb_articles)

    if not ai_result:
        # Graceful fallback redirect with error query parameter
        return RedirectResponse(
            url=f"/tickets/{ticket_id}?ai_error=true",
            status_code=status.HTTP_303_SEE_OTHER
        )

    # 3. Store AI Results in Ticket record
    now = datetime.now(timezone.utc)
    ticket.ai_summary = ai_result.summary
    ticket.suggested_resolution = (
        f"Recommended Priority: {ai_result.recommended_priority} | Difficulty: {ai_result.difficulty} (Confidence: {ai_result.confidence}%)\n"
        f"Root Cause: {ai_result.root_cause}\n\n"
        f"Troubleshooting Steps:\n" + "\n".join([f"- {s}" for s in ai_result.troubleshooting_steps]) + "\n\n"
        f"Suggested Fix:\n{ai_result.suggested_resolution}"
    )
    ticket.updated_at = now

    # Log AI Triage activity
    activity = TicketActivity(
        ticket_id=ticket.id,
        activity_type="AI_TRIAGED",
        notes=f"AI Triage completed (Confidence: {ai_result.confidence}%). Root Cause: {ai_result.root_cause}",
        created_at=now
    )
    db.add(activity)
    db.commit()

    return RedirectResponse(
        url=f"/tickets/{ticket_id}?triaged=true",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/api/tickets/{ticket_id}/triage")
async def trigger_ai_triage_api(
    ticket_id: int,
    db: Session = Depends(get_db)
):
    """REST API endpoint returning structured AI triage JSON."""
    ticket = TicketService.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    kb_articles = KBService.search_articles(db, query=ticket.title, category=ticket.category)[:5]
    if not kb_articles:
        kb_articles = KBService.get_all_articles(db, limit=5)

    ai_result = AIService.analyze_ticket(ticket, kb_articles)

    if not ai_result:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "AI analysis is currently unavailable. Please verify GROQ_API_KEY in .env."}
        )

    return ai_result


@router.post("/api/tickets/{ticket_id}/customer-reply")
async def generate_customer_reply_api(
    ticket_id: int,
    resolution_text: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """REST API endpoint to generate a customer-facing email response."""
    ticket = TicketService.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    reply = AIService.generate_customer_reply(ticket, resolution_text=resolution_text)

    if not reply:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "AI customer reply generation unavailable. Please verify GROQ_API_KEY."}
        )

    return reply
