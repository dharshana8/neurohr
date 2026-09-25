from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.models.user import User
from app.models.ai import AIChatConversation, HRPolicyDocument
from app.api.deps import (
    get_current_active_user,
    require_organization_admin,
    require_hr_manager,
    require_hr_analyst,
    require_recruiter
)
from app.services.ai.ai_service import AIService, get_org_id
from app.services.ai.policy_rag import PolicyRAGService
from app.services.ai.schemas import (
    AICopilotRequest,
    AICopilotResponse,
    ConversationSummary,
    AttritionExplainRequest,
    AttritionExplainResponse,
    CareerRecommendRequest,
    CareerRecommendResponse,
    RecruitmentExplainRequest,
    RecruitmentExplainResponse,
    SentimentSummaryRequest,
    SentimentSummaryResponse,
    PolicyUploadRequest,
    PolicyDocumentResponse,
    PolicyQueryRequest,
    PolicyQueryResponse
)

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# 1. AI HR COPILOT
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/copilot", response_model=AICopilotResponse)
async def chat_copilot(
    req: AICopilotRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Intelligent HR Copilot answering workforce, attrition, recruitment,
    skill gaps, and policy questions with verified organizational data.
    """
    try:
        return await AIService.chat_copilot(
            current_user=current_user,
            message=req.message,
            conversation_id=req.conversation_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/copilot/history", response_model=List[ConversationSummary])
async def get_copilot_history(
    current_user: User = Depends(get_current_active_user)
):
    org_id = get_org_id(current_user.organization_id)
    convs = await AIChatConversation.find({
        "organization_id.$id": org_id,
        "user_id.$id": current_user.id
    }).sort("-updated_at").to_list()

    return [
        ConversationSummary(
            conversation_id=c.conversation_id,
            title=c.title,
            message_count=len(c.messages),
            created_at=c.created_at,
            updated_at=c.updated_at
        ) for c in convs
    ]

@router.delete("/copilot/history/{conversation_id}")
async def delete_copilot_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user)
):
    org_id = get_org_id(current_user.organization_id)
    conv = await AIChatConversation.find_one({
        "conversation_id": conversation_id,
        "organization_id.$id": org_id,
        "user_id.$id": current_user.id
    })
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await conv.delete()
    return {"message": "Conversation deleted successfully"}

# ─────────────────────────────────────────────────────────────────────────────
# 2. ATTRITION EXPLANATION
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/explain/attrition", response_model=AttritionExplainResponse)
async def explain_attrition(
    req: AttritionExplainRequest,
    current_user: User = Depends(require_hr_analyst)
):
    """
    Translates attrition risk prediction and model SHAP factors into an executive summary.
    """
    try:
        return await AIService.explain_attrition(
            current_user=current_user,
            employee_id=req.employee_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────────────────────────────────────
# 3. CAREER RECOMMENDATION
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/explain/career", response_model=CareerRecommendResponse)
async def recommend_career(
    req: CareerRecommendRequest,
    current_user: User = Depends(require_hr_analyst)
):
    """
    Generates an AI-assisted career progression plan from actual deterministic skill gaps.
    """
    try:
        return await AIService.recommend_career_path(
            current_user=current_user,
            employee_id=req.employee_id,
            target_role=req.target_role
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────────────────────────────────────
# 4. RECRUITMENT EXPLANATION
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/explain/recruitment", response_model=RecruitmentExplainResponse)
async def explain_recruitment(
    req: RecruitmentExplainRequest,
    current_user: User = Depends(require_recruiter)
):
    """
    Translates candidate match scores and features into a recruiter briefing.
    """
    try:
        return await AIService.explain_recruitment_match(
            current_user=current_user,
            candidate_id=req.candidate_id,
            job_id=req.job_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────────────────────────────────────
# 5. SENTIMENT SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/summarize/sentiment", response_model=SentimentSummaryResponse)
async def summarize_sentiment(
    req: SentimentSummaryRequest,
    current_user: User = Depends(require_hr_analyst)
):
    """
    Summarizes aggregated employee sentiment feedback safely without PII.
    """
    try:
        return await AIService.summarize_sentiment(
            current_user=current_user,
            department=req.department
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────────────────────────────────────
# 6. HR POLICY RAG
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/policies/upload", response_model=PolicyDocumentResponse)
async def upload_policy(
    req: PolicyUploadRequest,
    current_user: User = Depends(require_hr_manager)
):
    """
    Upload and index an HR policy document with tenant-isolated chunking.
    """
    org_id = get_org_id(current_user.organization_id)
    doc = await PolicyRAGService.index_document(
        org_id=org_id,
        title=req.title,
        content=req.content,
        category=req.category
    )
    return PolicyDocumentResponse(
        document_id=doc.document_id,
        title=doc.title,
        category=doc.category,
        chunk_count=len(doc.chunks),
        created_at=doc.created_at
    )

@router.get("/policies", response_model=List[PolicyDocumentResponse])
async def list_policies(
    current_user: User = Depends(get_current_active_user)
):
    org_id = get_org_id(current_user.organization_id)
    docs = await HRPolicyDocument.find({"organization_id.$id": org_id}).sort("-created_at").to_list()
    return [
        PolicyDocumentResponse(
            document_id=d.document_id,
            title=d.title,
            category=d.category,
            chunk_count=len(d.chunks),
            created_at=d.created_at
        ) for d in docs
    ]

@router.delete("/policies/{document_id}")
async def delete_policy(
    document_id: str,
    current_user: User = Depends(require_hr_manager)
):
    """Delete an HR policy document and purge its chunks from the RAG knowledge index."""
    org_id = get_org_id(current_user.organization_id)
    doc = await HRPolicyDocument.find_one({
        "document_id": document_id,
        "organization_id.$id": org_id
    })
    if not doc:
        raise HTTPException(status_code=404, detail="Policy document not found")
    await doc.delete()
    return {"message": "Policy document removed successfully"}

@router.post("/policies/query", response_model=PolicyQueryResponse)
async def query_policy(
    req: PolicyQueryRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Ask question against organization's uploaded HR policies.
    """
    try:
        return await AIService.query_policy_rag(
            current_user=current_user,
            query=req.query
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
