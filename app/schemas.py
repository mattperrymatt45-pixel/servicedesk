from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


# ==========================================
# Ticket Activity Schemas
# ==========================================
class TicketActivityBase(BaseModel):
    activity_type: str = Field(..., description="Type of activity, e.g., CREATED, STATUS_CHANGE, AI_TRIAGED, RESOLVED")
    notes: Optional[str] = Field(None, description="Detailed notes regarding activity")


class TicketActivityCreate(TicketActivityBase):
    ticket_id: int


class TicketActivityRead(TicketActivityBase):
    id: int
    ticket_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Ticket Schemas
# ==========================================
class TicketBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Brief summary of the support issue")
    description: str = Field(..., min_length=5, description="Full details of the support issue")
    category: str = Field(default="General IT", max_length=100, description="Issue category")
    priority: str = Field(default="Medium", description="Ticket priority: Low, Medium, High, Urgent")


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    ai_summary: Optional[str] = None
    suggested_resolution: Optional[str] = None
    final_resolution: Optional[str] = None


class TicketRead(TicketBase):
    id: int
    status: str
    ai_summary: Optional[str] = None
    suggested_resolution: Optional[str] = None
    final_resolution: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    activities: List[TicketActivityRead] = []

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# KB Article Schemas
# ==========================================
class KBArticleBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Title of KB article")
    category: str = Field(..., max_length=100, description="Article category")
    problem: str = Field(..., min_length=5, description="Problem description or symptoms")
    solution: str = Field(..., min_length=5, description="Step-by-step fix or guidance")
    keywords: Optional[str] = Field(None, description="Comma-separated tags or keywords")


class KBArticleCreate(KBArticleBase):
    pass


class KBArticleRead(KBArticleBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# AI Service Schemas (Phase 4)
# ==========================================
class AITriageResult(BaseModel):
    summary: str = Field(..., description="Concise summary of the incident")
    recommended_category: str = Field(..., description="Recommended ticket category")
    recommended_priority: str = Field(..., description="Recommended ticket priority (Low, Medium, High, Urgent)")
    root_cause: str = Field(..., description="Probable root cause analysis")
    troubleshooting_steps: List[str] = Field(..., description="Actionable troubleshooting steps for engineer")
    suggested_resolution: str = Field(..., description="Recommended resolution guide")
    confidence: int = Field(default=85, ge=0, le=100, description="AI confidence score 0-100%")
    difficulty: str = Field(default="Medium", description="Estimated fix difficulty: Easy, Medium, Hard, Complex")


class AICustomerReply(BaseModel):
    greeting: str = Field(..., description="Polite customer greeting")
    body: str = Field(..., description="Non-technical, clear explanation of status/fix")
    closing: str = Field(..., description="Friendly closing sign-off")
    full_reply: str = Field(..., description="Complete combined customer reply email text")
