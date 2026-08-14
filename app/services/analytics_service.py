from sqlalchemy.orm import Session
from sqlalchemy import func, or_, text
from datetime import datetime, timezone
from typing import Dict, Any, List

from app.models import Ticket, KBArticle, TicketActivity


class AnalyticsService:
    """Service layer providing SQL metrics and chart data for the Analytics Dashboard."""

    @staticmethod
    def get_dashboard_metrics(db: Session) -> Dict[str, Any]:
        """Fetch high-level KPI metrics for top stat cards."""
        total_tickets = db.query(Ticket).count()
        open_tickets = db.query(Ticket).filter(Ticket.status == "Open").count()
        in_progress_tickets = db.query(Ticket).filter(Ticket.status == "In Progress").count()
        resolved_tickets = db.query(Ticket).filter(Ticket.status == "Resolved").count()
        
        urgent_tickets = db.query(Ticket).filter(
            or_(Ticket.priority == "Urgent", Ticket.priority == "Critical")
        ).count()
        high_tickets = db.query(Ticket).filter(Ticket.priority == "High").count()

        # Count AI Analyses performed
        ai_analyses = db.query(TicketActivity).filter(
            TicketActivity.activity_type == "AI_TRIAGED"
        ).count()
        if ai_analyses == 0:
            ai_analyses = db.query(Ticket).filter(Ticket.ai_summary != None).count()

        # Count Total KB Articles
        total_kb = db.query(KBArticle).count()

        # Calculate Average Resolution Time (in hours)
        resolved_items = db.query(Ticket).filter(
            Ticket.status == "Resolved", Ticket.updated_at != None, Ticket.created_at != None
        ).all()

        if resolved_items:
            durations = []
            for t in resolved_items:
                delta = t.updated_at - t.created_at
                hours = delta.total_seconds() / 3600.0
                if hours >= 0:
                    durations.append(hours)
            avg_res_hours = round(sum(durations) / len(durations), 1) if durations else 0.0
        else:
            avg_res_hours = 0.0

        return {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "in_progress_tickets": in_progress_tickets,
            "resolved_tickets": resolved_tickets,
            "urgent_tickets": urgent_tickets,
            "high_tickets": high_tickets,
            "ai_analyses": ai_analyses,
            "total_kb": total_kb,
            "avg_resolution_hours": avg_res_hours
        }

    @staticmethod
    def get_chart_data(db: Session) -> Dict[str, Any]:
        """Fetch aggregated distributions for Chart.js visualization."""
        # 1. Status Distribution
        status_rows = db.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
        status_data = {r[0]: r[1] for r in status_rows}

        # 2. Priority Distribution
        priority_rows = db.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()
        priority_data = {r[0]: r[1] for r in priority_rows}

        # 3. Category Distribution
        cat_rows = db.query(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category).order_by(func.count(Ticket.id).desc()).limit(8).all()
        category_labels = [r[0] for r in cat_rows]
        category_counts = [r[1] for r in cat_rows]

        # 4. Ticket Creation Trend (Grouped by Date)
        trend_rows = db.query(
            func.date(Ticket.created_at).label("created_date"),
            func.count(Ticket.id)
        ).group_by(func.date(Ticket.created_at)).order_by("created_date").limit(10).all()

        trend_labels = [str(r[0]) for r in trend_rows]
        trend_counts = [r[1] for r in trend_rows]

        return {
            "status": {
                "labels": list(status_data.keys()),
                "counts": list(status_data.values())
            },
            "priority": {
                "labels": list(priority_data.keys()),
                "counts": list(priority_data.values())
            },
            "category": {
                "labels": category_labels,
                "counts": category_counts
            },
            "trend": {
                "labels": trend_labels,
                "counts": trend_counts
            }
        }
