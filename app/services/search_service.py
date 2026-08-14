import re
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Dict, Any, List, Tuple

from app.models import Ticket, KBArticle


class SearchService:
    """Service layer for unified global search across support tickets and knowledge base articles."""

    @staticmethod
    def global_search(db: Session, query: str) -> Tuple[List[Ticket], List[KBArticle]]:
        """
        Execute unified global search.
        Matches against Ticket Title, Description, ID and KB Title, Problem, Keywords.
        """
        if not query or not query.strip():
            return [], []

        clean_q = query.strip()
        q_term = f"%{clean_q}%"

        # Check if query matches a ticket ID pattern like "TCK-1" or "1"
        id_match = re.search(r'(\d+)', clean_q)
        matched_id = int(id_match.group(1)) if id_match else None

        # 1. Search Tickets
        ticket_filter = or_(
            Ticket.title.ilike(q_term),
            Ticket.description.ilike(q_term),
            Ticket.category.ilike(q_term)
        )
        if matched_id:
            ticket_filter = or_(ticket_filter, Ticket.id == matched_id)

        ticket_results = db.query(Ticket).filter(ticket_filter).order_by(Ticket.created_at.desc()).limit(20).all()

        # 2. Search KB Articles
        kb_results = db.query(KBArticle).filter(
            or_(
                KBArticle.title.ilike(q_term),
                KBArticle.problem.ilike(q_term),
                KBArticle.solution.ilike(q_term),
                KBArticle.keywords.ilike(q_term),
                KBArticle.category.ilike(q_term)
            )
        ).order_by(KBArticle.created_at.desc()).limit(20).all()

        return ticket_results, kb_results
