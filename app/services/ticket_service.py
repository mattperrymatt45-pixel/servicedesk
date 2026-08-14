from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional, Tuple, Dict, Any

from app.models import Ticket, TicketActivity
from app.schemas import TicketCreate, TicketUpdate


class TicketService:
    """Service layer encapsulating ticket lifecycle management, search, and activity logs."""

    @staticmethod
    def get_all_tickets(
        db: Session,
        query: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Ticket], int]:
        """
        Search and filter tickets with pagination.
        Returns tuple of (tickets_list, total_filtered_count).
        """
        stmt = db.query(Ticket)

        if query and query.strip():
            q_term = f"%{query.strip()}%"
            stmt = stmt.filter(
                or_(
                    Ticket.title.ilike(q_term),
                    Ticket.description.ilike(q_term),
                    Ticket.category.ilike(q_term)
                )
            )

        if status and status.strip() and status != "All":
            stmt = stmt.filter(func.lower(Ticket.status) == func.lower(status.strip()))

        if priority and priority.strip() and priority != "All":
            stmt = stmt.filter(func.lower(Ticket.priority) == func.lower(priority.strip()))

        if category and category.strip() and category != "All":
            stmt = stmt.filter(func.lower(Ticket.category) == func.lower(category.strip()))

        total_count = stmt.count()
        tickets = stmt.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()

        return tickets, total_count

    @staticmethod
    def get_ticket_by_id(db: Session, ticket_id: int) -> Optional[Ticket]:
        """Fetch a ticket by ID."""
        return db.query(Ticket).filter(Ticket.id == ticket_id).first()

    @staticmethod
    def create_ticket(db: Session, ticket_in: TicketCreate) -> Ticket:
        """Create a new ticket and record initial CREATED activity log."""
        now = datetime.now(timezone.utc)
        ticket = Ticket(
            title=ticket_in.title.strip(),
            description=ticket_in.description.strip(),
            category=ticket_in.category.strip() if ticket_in.category else "General IT",
            priority=ticket_in.priority.strip() if ticket_in.priority else "Medium",
            status="Open",
            created_at=now,
            updated_at=now
        )
        db.add(ticket)
        db.flush()

        # Log creation activity
        activity = TicketActivity(
            ticket_id=ticket.id,
            activity_type="CREATED",
            notes=f"Ticket created with priority '{ticket.priority}' in category '{ticket.category}'",
            created_at=now
        )
        db.add(activity)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def update_ticket(db: Session, ticket_id: int, ticket_in: TicketUpdate) -> Optional[Ticket]:
        """Update ticket properties and record appropriate activity logs."""
        ticket = TicketService.get_ticket_by_id(db, ticket_id)
        if not ticket:
            return None

        now = datetime.now(timezone.utc)
        changes = []

        if ticket_in.title and ticket_in.title.strip() != ticket.title:
            ticket.title = ticket_in.title.strip()
            changes.append("Title updated")

        if ticket_in.description and ticket_in.description.strip() != ticket.description:
            ticket.description = ticket_in.description.strip()
            changes.append("Description updated")

        if ticket_in.category and ticket_in.category.strip() != ticket.category:
            old_cat = ticket.category
            ticket.category = ticket_in.category.strip()
            changes.append(f"Category changed from '{old_cat}' to '{ticket.category}'")

        if ticket_in.priority and ticket_in.priority.strip() != ticket.priority:
            old_pri = ticket.priority
            ticket.priority = ticket_in.priority.strip()
            changes.append(f"Priority changed from '{old_pri}' to '{ticket.priority}'")

        if ticket_in.status and ticket_in.status.strip() != ticket.status:
            old_status = ticket.status
            ticket.status = ticket_in.status.strip()
            changes.append(f"Status changed from '{old_status}' to '{ticket.status}'")

        if changes:
            ticket.updated_at = now
            activity = TicketActivity(
                ticket_id=ticket.id,
                activity_type="EDITED",
                notes="; ".join(changes),
                created_at=now
            )
            db.add(activity)
            db.commit()
            db.refresh(ticket)

        return ticket

    @staticmethod
    def add_internal_note(db: Session, ticket_id: int, note_text: str) -> Optional[TicketActivity]:
        """Add internal support engineer note to ticket activity timeline."""
        ticket = TicketService.get_ticket_by_id(db, ticket_id)
        if not ticket:
            return None

        now = datetime.now(timezone.utc)
        ticket.updated_at = now

        activity = TicketActivity(
            ticket_id=ticket.id,
            activity_type="NOTE_ADDED",
            notes=note_text.strip(),
            created_at=now
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity

    @staticmethod
    def resolve_ticket(db: Session, ticket_id: int, resolution_notes: str) -> Optional[Ticket]:
        """Mark ticket as Resolved and store final resolution text and timestamp."""
        ticket = TicketService.get_ticket_by_id(db, ticket_id)
        if not ticket:
            return None

        now = datetime.now(timezone.utc)
        ticket.status = "Resolved"
        ticket.final_resolution = resolution_notes.strip()
        ticket.updated_at = now

        activity = TicketActivity(
            ticket_id=ticket.id,
            activity_type="RESOLVED",
            notes=f"Ticket marked as Resolved. Notes: {resolution_notes.strip()}",
            created_at=now
        )
        db.add(activity)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def delete_ticket(db: Session, ticket_id: int) -> bool:
        """Delete a ticket and its associated activity records."""
        ticket = TicketService.get_ticket_by_id(db, ticket_id)
        if not ticket:
            return False

        db.delete(ticket)
        db.commit()
        return True

    @staticmethod
    def get_categories(db: Session) -> List[str]:
        """Return distinct category list."""
        result = db.query(Ticket.category).distinct().all()
        categories = sorted([r[0] for r in result if r[0]])
        return categories or ["General IT", "Network & VPN", "Access Management", "Email & Collaboration", "Laptop / Endpoint", "Printers & Devices", "Security"]

    @staticmethod
    def get_ticket_counts(db: Session) -> Dict[str, int]:
        """Return counts by status for metrics overview."""
        return {
            "total": db.query(Ticket).count(),
            "open": db.query(Ticket).filter(Ticket.status == "Open").count(),
            "in_progress": db.query(Ticket).filter(Ticket.status == "In Progress").count(),
            "resolved": db.query(Ticket).filter(Ticket.status == "Resolved").count(),
            "closed": db.query(Ticket).filter(Ticket.status == "Closed").count(),
        }
