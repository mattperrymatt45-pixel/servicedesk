from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="Open")  # Open, In Progress, Pending, Resolved, Closed
    priority = Column(String(50), nullable=False, default="Medium")  # Low, Medium, High, Urgent
    category = Column(String(100), nullable=False, default="General IT")
    
    # AI-assisted fields
    ai_summary = Column(Text, nullable=True)
    suggested_resolution = Column(Text, nullable=True)
    
    # Final resolution tracking
    final_resolution = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    activities = relationship("TicketActivity", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketActivity.created_at.desc()")


class KBArticle(Base):
    __tablename__ = "kb_articles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    problem = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    keywords = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class TicketActivity(Base):
    __tablename__ = "ticket_activities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    activity_type = Column(String(100), nullable=False)  # CREATED, STATUS_CHANGE, AI_TRIAGED, RESOLVED, COMMENT
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    ticket = relationship("Ticket", back_populates="activities")
