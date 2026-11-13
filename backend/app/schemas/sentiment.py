from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class FeedbackCreate(BaseModel):
    department: str
    category: str
    feedback_text: str
    source: Optional[str] = "SURVEY"
    employee_id: Optional[str] = None
    submitted_at: Optional[datetime] = None


class FeedbackUpdate(BaseModel):
    department: Optional[str] = None
    category: Optional[str] = None
    feedback_text: Optional[str] = None
    source: Optional[str] = None
    employee_id: Optional[str] = None


class SentimentScoreBreakdown(BaseModel):
    positive: float
    neutral: float
    negative: float
    compound: float


class SentimentResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sentiment_id: str
    feedback_id: str
    employee_id: Optional[str] = None
    sentiment: str
    sentiment_score: Dict[str, float]
    model_name: str
    model_version: str
    analyzed_at: datetime


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    feedback_id: str
    employee_id: Optional[str] = None
    department: str
    category: str
    feedback_text: str
    source: str
    submitted_at: datetime
    is_synthetic: bool = False
    sentiment_result: Optional[SentimentResultResponse] = None
    created_at: datetime
    updated_at: datetime


class FeedbackListResponse(BaseModel):
    items: List[FeedbackResponse]
    total: int
    page: int
    limit: int


class BatchAnalysisResponse(BaseModel):
    total_evaluated: int
    analyzed_count: int
    skipped_count: int
    sentiment_counts: Dict[str, int]


class DepartmentSentimentItem(BaseModel):
    department: str
    total_feedback: int
    positive_count: int
    neutral_count: int
    negative_count: int
    positive_pct: float
    neutral_pct: float
    negative_pct: float


class DepartmentSentimentResponse(BaseModel):
    departments: List[DepartmentSentimentItem]
    total_feedback: int


class TrendSentimentPoint(BaseModel):
    period: str
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    total_count: int


class TrendSentimentResponse(BaseModel):
    trends: List[TrendSentimentPoint]
    timeframe: str


class ThemeItem(BaseModel):
    theme: str
    count: int
    percentage: float
    positive_count: int
    neutral_count: int
    negative_count: int


class ThemeAnalysisResponse(BaseModel):
    themes: List[ThemeItem]
    total_categorized: int


class AIInsightRequest(BaseModel):
    department: Optional[str] = None
    timeframe: Optional[str] = None


class AIInsightResponse(BaseModel):
    insight: str
    overall_sentiment: Dict[str, float]
    top_themes: List[str]
    department_summary: Optional[Dict[str, Any]] = None
    generated_at: datetime
    is_ai_assisted: bool = True
    model: str = "grok-4.6"
    disclaimer: str = "AI-generated executive summary based strictly on stored workplace sentiment data."


class FeedbackImportSummary(BaseModel):
    total_rows: int
    imported_count: int
    errors: List[str]
