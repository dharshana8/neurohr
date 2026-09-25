from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# --- Chat & Copilot ---
class ChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str
    sources: Optional[List[str]] = None
    timestamp: Optional[str] = None

class AICopilotRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None

class AICopilotResponse(BaseModel):
    answer: str
    conversation_id: str
    sources: List[str] = Field(default_factory=list)
    supporting_data: Optional[Dict[str, Any]] = None
    is_ai_assisted: bool = True
    demo_mode: bool = False
    disclaimer: str = "AI-assisted response. Decision support only; verify with official records."

class ConversationSummary(BaseModel):
    conversation_id: str
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Attrition Explanation ---
class AttritionExplainRequest(BaseModel):
    employee_id: str = Field(..., min_length=1)

class AttritionExplainResponse(BaseModel):
    employee_id: str
    risk_level: str
    risk_score: float
    probability: Optional[float] = None
    model_factors: List[Dict[str, Any]] = Field(default_factory=list)
    top_risk_factors: Optional[List[Dict[str, Any]]] = None
    protective_factors: Optional[List[Dict[str, Any]]] = None
    ai_explanation: str
    ai_narrative: Optional[str] = None
    is_ai_assisted: bool = True
    disclaimer: str = "AI-generated explanation based strictly on model SHAP factors. Does not replace human management evaluation."

# --- Career Recommendations ---
class DevelopmentAreaItem(BaseModel):
    skill: str
    reason: str
    recommended_action: str

class CareerRecommendRequest(BaseModel):
    employee_id: str = Field(..., min_length=1)
    target_role: str = Field(..., min_length=1)

class CareerRecommendResponse(BaseModel):
    employee_id: str
    current_role: str
    target_role: str
    summary: str
    development_areas: List[DevelopmentAreaItem]
    milestones: List[str]
    is_ai_assisted: bool = True
    disclaimer: str = "AI-assisted recommendation for development planning. Does not constitute a guaranteed promotion."

# --- Recruitment Explanation ---
class RecruitmentExplainRequest(BaseModel):
    candidate_id: str = Field(..., min_length=1)
    job_id: str = Field(..., min_length=1)

class RecruitmentExplainResponse(BaseModel):
    candidate_id: str
    candidate_name: str
    job_id: str
    job_title: str
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    experience_verdict: str
    ai_explanation: str
    is_ai_assisted: bool = True
    disclaimer: str = "AI-generated match explanation based on deterministic algorithm results. Human reviewer makes final candidate decision."

# --- Sentiment Summary ---
class SentimentSummaryRequest(BaseModel):
    department: Optional[str] = None

class SentimentSummaryResponse(BaseModel):
    department: str
    total_feedbacks: int
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    ai_summary: str
    is_ai_assisted: bool = True
    disclaimer: str = "Aggregated sentiment summary based strictly on anonymized employee feedback metrics."

# --- Policy RAG ---
class PolicyUploadRequest(BaseModel):
    title: str = Field(..., min_length=1)
    category: str = "General Policy"
    content: str = Field(..., min_length=10)

class PolicyDocumentResponse(BaseModel):
    document_id: str
    title: str
    category: str
    chunk_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PolicyQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)

class PolicyQueryResponse(BaseModel):
    answer: str
    sources: List[str]
    matched_chunks: List[str]
    is_ai_assisted: bool = True
    disclaimer: str = "Generated strictly from retrieved organization policy documentation."
