from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from pydantic import Field
from beanie import Document, Link
from app.models.organization import Organization


class EmployeeFeedback(Document):
    feedback_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Link[Organization]
    employee_id: Optional[str] = None
    department: str
    category: str  # ENGAGEMENT, WORKPLACE, MANAGEMENT, CULTURE, WORKLOAD, CAREER, BENEFITS, EXIT, OTHER
    feedback_text: str
    source: str = "SURVEY"  # SURVEY, HR_FORM, MANAGER_FEEDBACK, EXIT_FEEDBACK, OTHER
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_synthetic: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "employee_feedbacks"
        indexes = [
            "feedback_id",
            "organization_id",
            "department",
            "category",
            "submitted_at",
            "source"
        ]


class SentimentResult(Document):
    sentiment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Link[Organization]
    feedback_id: str
    employee_id: Optional[str] = None
    sentiment: str  # POSITIVE, NEUTRAL, NEGATIVE
    sentiment_score: Dict[str, float] = Field(default_factory=dict)  # {"positive": 0.82, "neutral": 0.12, "negative": 0.06, "compound": 0.76}
    model_name: str = "vader-sentiment"
    model_version: str = "3.3.2"
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "sentiment_results"
        indexes = [
            "sentiment_id",
            "organization_id",
            "feedback_id",
            "sentiment",
            "analyzed_at"
        ]
