from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import Field
from beanie import Document, Link
from app.models.organization import Organization

class AttritionPrediction(Document):
    organization_id: Link[Organization]
    employee_id: str
    probability: float
    risk_level: str  # LOW, MEDIUM, HIGH
    model_version: str = "demo-v1"
    top_factors: Dict[str, Any] = Field(default_factory=dict)  # SHAP output
    features_used: Dict[str, Any] = Field(default_factory=dict)
    
    prediction_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "attrition_predictions"
        indexes = [
            "organization_id",
            "employee_id",
            "prediction_date",
            "risk_level"
        ]

