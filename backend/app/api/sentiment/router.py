import csv
import io
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File

from app.models.user import User
from app.models.sentiment import EmployeeFeedback, SentimentResult
from app.models.audit import AuditLog
from app.schemas.sentiment import (
    FeedbackCreate, FeedbackUpdate, FeedbackResponse, FeedbackListResponse,
    SentimentResultResponse, BatchAnalysisResponse,
    DepartmentSentimentItem, DepartmentSentimentResponse,
    TrendSentimentPoint, TrendSentimentResponse,
    ThemeItem, ThemeAnalysisResponse,
    AIInsightRequest, AIInsightResponse,
    FeedbackImportSummary
)
from app.api.deps import (
    require_hr_manager,
    require_hr_analyst,
    require_organization_admin,
    get_current_active_user
)
from app.intelligence.services.sentiment_service import (
    SentimentAnalysisService,
    get_org_id
)

router = APIRouter()


def check_tenant_access(current_user: User):
    """Ensure user has a valid organization context. Reject Platform Admin or detached users."""
    if current_user.role == "PLATFORM_ADMIN" or not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform administrators and unassigned users cannot access organization-specific workplace sentiment data."
        )


def can_view_employee_id(current_user: User) -> bool:
    """Only Organization Admins and HR Managers can view identifiable employee IDs."""
    return current_user.role in ["ORGANIZATION_ADMIN", "HR_MANAGER"]


# ─────────────────────────────────────────────────────────────────────────────
# 1. FEEDBACK CRUD ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(
    req: FeedbackCreate,
    current_user: User = Depends(require_hr_manager)
):
    check_tenant_access(current_user)
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    if not req.feedback_text.strip():
        raise HTTPException(status_code=400, detail="Feedback text cannot be empty")

    now = datetime.now(timezone.utc)
    fb = EmployeeFeedback(
        organization_id=org_ref,
        employee_id=req.employee_id.strip() if req.employee_id else None,
        department=req.department.strip(),
        category=req.category.strip().upper(),
        feedback_text=req.feedback_text.strip(),
        source=req.source.strip().upper() if req.source else "SURVEY",
        submitted_at=req.submitted_at or now,
        created_at=now,
        updated_at=now
    )
    await fb.insert()

    # Automatically analyze sentiment for new feedback
    sentiment_res = await SentimentAnalysisService.analyze_feedback(fb)

    # Privacy-conscious Audit Logging: Never record complete feedback text
    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="FEEDBACK_CREATED",
        resource_type="EmployeeFeedback",
        resource_id=fb.feedback_id,
        status="SUCCESS"
    ).insert()

    return FeedbackResponse(
        id=str(fb.id),
        feedback_id=fb.feedback_id,
        employee_id=fb.employee_id if can_view_employee_id(current_user) else None,
        department=fb.department,
        category=fb.category,
        feedback_text=fb.feedback_text,
        source=fb.source,
        submitted_at=fb.submitted_at,
        is_synthetic=fb.is_synthetic,
        sentiment_result=SentimentResultResponse(
            sentiment_id=sentiment_res.sentiment_id,
            feedback_id=sentiment_res.feedback_id,
            employee_id=sentiment_res.employee_id if can_view_employee_id(current_user) else None,
            sentiment=sentiment_res.sentiment,
            sentiment_score=sentiment_res.sentiment_score,
            model_name=sentiment_res.model_name,
            model_version=sentiment_res.model_version,
            analyzed_at=sentiment_res.analyzed_at
        ),
        created_at=fb.created_at,
        updated_at=fb.updated_at
    )


@router.get("/feedback", response_model=FeedbackListResponse)
async def list_feedbacks(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_hr_analyst)
):
    check_tenant_access(current_user)
    org_id = get_org_id(current_user.organization_id)

    query: Dict[str, Any] = {"organization_id.$id": org_id}
    if category and category.upper() != "ALL":
        query["category"] = category.upper()
    if department and department.upper() != "ALL":
        query["department"] = department
    if source and source.upper() != "ALL":
        query["source"] = source.upper()

    # If filtering by sentiment, find matching feedback IDs first
    if sentiment and sentiment.upper() != "ALL":
        s_res = await SentimentResult.find({
            "organization_id.$id": org_id,
            "sentiment": sentiment.upper()
        }).to_list()
        matching_fb_ids = [r.feedback_id for r in s_res]
        query["feedback_id"] = {"$in": matching_fb_ids}

    # Retrieve all or filtered
    feedbacks = await EmployeeFeedback.find(query).sort("-submitted_at").to_list()

    # Search filter in-memory on feedback text or category/department
    if search:
        s_low = search.lower()
        feedbacks = [
            f for f in feedbacks
            if s_low in f.feedback_text.lower()
            or s_low in f.department.lower()
            or s_low in f.category.lower()
            or (f.employee_id and s_low in f.employee_id.lower() and can_view_employee_id(current_user))
        ]

    total = len(feedbacks)
    start = (page - 1) * limit
    paginated_feedbacks = feedbacks[start:start + limit]

    # Preload sentiments
    fb_ids = [f.feedback_id for f in paginated_feedbacks]
    sentiment_list = await SentimentResult.find({
        "organization_id.$id": org_id,
        "feedback_id": {"$in": fb_ids}
    }).to_list()
    sentiments_map = {r.feedback_id: r for r in sentiment_list}

    items = []
    view_emp = can_view_employee_id(current_user)
    for fb in paginated_feedbacks:
        s_res = sentiments_map.get(fb.feedback_id)
        s_dto = None
        if s_res:
            s_dto = SentimentResultResponse(
                sentiment_id=s_res.sentiment_id,
                feedback_id=s_res.feedback_id,
                employee_id=s_res.employee_id if view_emp else None,
                sentiment=s_res.sentiment,
                sentiment_score=s_res.sentiment_score,
                model_name=s_res.model_name,
                model_version=s_res.model_version,
                analyzed_at=s_res.analyzed_at
            )

        items.append(
            FeedbackResponse(
                id=str(fb.id),
                feedback_id=fb.feedback_id,
                employee_id=fb.employee_id if view_emp else None,
                department=fb.department,
                category=fb.category,
                feedback_text=fb.feedback_text,
                source=fb.source,
                submitted_at=fb.submitted_at,
                is_synthetic=fb.is_synthetic,
                sentiment_result=s_dto,
                created_at=fb.created_at,
                updated_at=fb.updated_at
            )
        )

    return FeedbackListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: str,
    current_user: User = Depends(require_hr_analyst)
):
    check_tenant_access(current_user)
    org_id = get_org_id(current_user.organization_id)

    fb = await EmployeeFeedback.find_one({
        "feedback_id": feedback_id,
        "organization_id.$id": org_id
    })
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback record not found")

    s_res = await SentimentResult.find_one({
        "feedback_id": feedback_id,
        "organization_id.$id": org_id
    })

    view_emp = can_view_employee_id(current_user)
    s_dto = None
    if s_res:
        s_dto = SentimentResultResponse(
            sentiment_id=s_res.sentiment_id,
            feedback_id=s_res.feedback_id,
            employee_id=s_res.employee_id if view_emp else None,
            sentiment=s_res.sentiment,
            sentiment_score=s_res.sentiment_score,
            model_name=s_res.model_name,
            model_version=s_res.model_version,
            analyzed_at=s_res.analyzed_at
        )

    return FeedbackResponse(
        id=str(fb.id),
        feedback_id=fb.feedback_id,
        employee_id=fb.employee_id if view_emp else None,
        department=fb.department,
        category=fb.category,
        feedback_text=fb.feedback_text,
        source=fb.source,
        submitted_at=fb.submitted_at,
        is_synthetic=fb.is_synthetic,
        sentiment_result=s_dto,
        created_at=fb.created_at,
        updated_at=fb.updated_at
    )


@router.put("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: str,
    req: FeedbackUpdate,
    current_user: User = Depends(require_hr_manager)
):
    check_tenant_access(current_user)
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    fb = await EmployeeFeedback.find_one({
        "feedback_id": feedback_id,
        "organization_id.$id": org_id
    })
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback record not found")

    text_changed = False
    if req.feedback_text is not None and req.feedback_text.strip():
        if req.feedback_text.strip() != fb.feedback_text:
            fb.feedback_text = req.feedback_text.strip()
            text_changed = True

    if req.department is not None and req.department.strip():
        fb.department = req.department.strip()
    if req.category is not None and req.category.strip():
        fb.category = req.category.strip().upper()
    if req.source is not None and req.source.strip():
        fb.source = req.source.strip().upper()
    if req.employee_id is not None:
        fb.employee_id = req.employee_id.strip() if req.employee_id.strip() else None

    fb.updated_at = datetime.now(timezone.utc)
    await fb.save()

    # Re-analyze if text changed
    sentiment_res = await SentimentAnalysisService.analyze_feedback(fb, force_reanalyze=text_changed)

    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="FEEDBACK_UPDATED",
        resource_type="EmployeeFeedback",
        resource_id=feedback_id,
        status="SUCCESS"
    ).insert()

    view_emp = can_view_employee_id(current_user)
    return FeedbackResponse(
        id=str(fb.id),
        feedback_id=fb.feedback_id,
        employee_id=fb.employee_id if view_emp else None,
        department=fb.department,
        category=fb.category,
        feedback_text=fb.feedback_text,
        source=fb.source,
        submitted_at=fb.submitted_at,
        is_synthetic=fb.is_synthetic,
        sentiment_result=SentimentResultResponse(
            sentiment_id=sentiment_res.sentiment_id,
            feedback_id=sentiment_res.feedback_id,
            employee_id=sentiment_res.employee_id if view_emp else None,
            sentiment=sentiment_res.sentiment,
            sentiment_score=sentiment_res.sentiment_score,
            model_name=sentiment_res.model_name,
            model_version=sentiment_res.model_version,
            analyzed_at=sentiment_res.analyzed_at
        ),
        created_at=fb.created_at,
        updated_at=fb.updated_at
    )


@router.delete("/feedback/actions/clear-all")
async def clear_all_feedback(
    current_user: User = Depends(require_hr_manager)
):
    """Delete all feedback records and associated sentiment results for the organization."""
    check_tenant_access(current_user)
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    feedbacks = await EmployeeFeedback.find({"organization_id.$id": org_id}).to_list()
    count = len(feedbacks)

    await SentimentResult.find({"organization_id.$id": org_id}).delete()
    await EmployeeFeedback.find({"organization_id.$id": org_id}).delete()

    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="FEEDBACK_ALL_CLEARED",
        resource_type="EmployeeFeedback",
        resource_id=f"count:{count}",
        status="SUCCESS"
    ).insert()

    return {"message": f"Successfully deleted all {count} feedback records", "count": count}


@router.delete("/feedback/{feedback_id}")
async def delete_feedback(
    feedback_id: str,
    current_user: User = Depends(require_hr_manager)
):
    check_tenant_access(current_user)
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    fb = await EmployeeFeedback.find_one({
        "feedback_id": feedback_id,
        "organization_id.$id": org_id
    })
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback record not found")

    await fb.delete()
    # Also remove associated sentiment result
    await SentimentResult.find({
        "feedback_id": feedback_id,
        "organization_id.$id": org_id
    }).delete()

    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="FEEDBACK_DELETED",
        resource_type="EmployeeFeedback",
        resource_id=feedback_id,
        status="SUCCESS"
    ).insert()

    return {"message": "Feedback record deleted successfully"}


# ─────────────────────────────────────────────────────────────────────────────
# 2. CSV IMPORT ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/feedback/import", response_model=FeedbackImportSummary)
async def import_feedback_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_hr_manager)
):
    check_tenant_access(current_user)
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except Exception:
        text = content.decode("latin1")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file is empty or formatted incorrectly.")

    # Required columns check
    required_cols = {"feedback_text", "department", "category"}
    present_cols = {c.strip().lower() for c in reader.fieldnames if c}
    if not required_cols.issubset(present_cols):
        missing = required_cols - present_cols
        raise HTTPException(status_code=400, detail=f"Missing required columns in CSV: {', '.join(missing)}")

    # Case-insensitive column mapper
    col_map = {c.strip().lower(): c for c in reader.fieldnames if c}

    total_rows = 0
    imported = 0
    errors = []
    feedbacks_to_insert = []
    now = datetime.now(timezone.utc)

    for idx, row in enumerate(reader, start=2):
        total_rows += 1
        text_val = row.get(col_map["feedback_text"], "").strip()
        dept_val = row.get(col_map["department"], "").strip()
        cat_val = row.get(col_map["category"], "").strip()

        if not text_val or not dept_val or not cat_val:
            errors.append(f"Row {idx}: missing required field (feedback_text, department, or category)")
            continue

        fid = row.get(col_map.get("feedback_id", ""), "").strip()
        if not fid:
            fid = str(uuid.uuid4())

        emp_id = row.get(col_map.get("employee_id", ""), "").strip() or None
        src = row.get(col_map.get("source", ""), "SURVEY").strip().upper() or "SURVEY"

        sub_date = now
        sub_str = row.get(col_map.get("submitted_at", ""), "").strip()
        if sub_str:
            try:
                sub_date = datetime.fromisoformat(sub_str.replace("Z", "+00:00"))
            except Exception:
                pass

        fb = EmployeeFeedback(
            feedback_id=fid,
            organization_id=org_ref,
            employee_id=emp_id,
            department=dept_val,
            category=cat_val.upper(),
            feedback_text=text_val,
            source=src,
            submitted_at=sub_date,
            is_synthetic=True,  # Imported via bulk file
            created_at=now,
            updated_at=now
        )
        feedbacks_to_insert.append(fb)

    if feedbacks_to_insert:
        await EmployeeFeedback.insert_many(feedbacks_to_insert)
        # Batch analyze newly imported items
        await SentimentAnalysisService.analyze_batch(feedbacks_to_insert, force_reanalyze=False)
        imported = len(feedbacks_to_insert)

    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="FEEDBACK_BATCH_IMPORTED",
        resource_type="EmployeeFeedback",
        resource_id=f"count:{imported}",
        status="SUCCESS"
    ).insert()

    return FeedbackImportSummary(
        total_rows=total_rows,
        imported_count=imported,
        errors=errors[:20]
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. SENTIMENT ANALYSIS & BATCH ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/sentiment/analyze/{feedback_id}", response_model=SentimentResultResponse)
async def analyze_single_feedback(
    feedback_id: str,
    current_user: User = Depends(require_hr_analyst)
):
    check_tenant_access(current_user)
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    fb = await EmployeeFeedback.find_one({
        "feedback_id": feedback_id,
        "organization_id.$id": org_id
    })
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback record not found in this organization")

    res = await SentimentAnalysisService.analyze_feedback(fb, force_reanalyze=True)

    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="SENTIMENT_ANALYZED",
        resource_type="SentimentResult",
        resource_id=res.sentiment_id,
        status="SUCCESS"
    ).insert()

    view_emp = can_view_employee_id(current_user)
    return SentimentResultResponse(
        sentiment_id=res.sentiment_id,
        feedback_id=res.feedback_id,
        employee_id=res.employee_id if view_emp else None,
        sentiment=res.sentiment,
        sentiment_score=res.sentiment_score,
        model_name=res.model_name,
        model_version=res.model_version,
        analyzed_at=res.analyzed_at
    )


@router.post("/sentiment/analyze-all", response_model=BatchAnalysisResponse)
async def analyze_all_feedbacks(
    force: bool = Query(False),
    current_user: User = Depends(require_hr_analyst)
):
    check_tenant_access(current_user)
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    feedbacks = await EmployeeFeedback.find({"organization_id.$id": org_id}).to_list()
    total_eval, analyzed_cnt, skipped_cnt, counts = await SentimentAnalysisService.analyze_batch(
        feedbacks,
        force_reanalyze=force
    )

    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="SENTIMENT_BATCH_ANALYZED",
        resource_type="SentimentResult",
        resource_id=f"evaluated:{total_eval}_analyzed:{analyzed_cnt}",
        status="SUCCESS"
    ).insert()

    return BatchAnalysisResponse(
        total_evaluated=total_eval,
        analyzed_count=analyzed_cnt,
        skipped_count=skipped_cnt,
        sentiment_counts=counts
    )


@router.get("/sentiment/results/{feedback_id}", response_model=SentimentResultResponse)
async def get_sentiment_result(
    feedback_id: str,
    current_user: User = Depends(require_hr_analyst)
):
    check_tenant_access(current_user)
    org_id = get_org_id(current_user.organization_id)

    res = await SentimentResult.find_one({
        "feedback_id": feedback_id,
        "organization_id.$id": org_id
    })
    if not res:
        raise HTTPException(status_code=404, detail="Sentiment result not found for this feedback")

    view_emp = can_view_employee_id(current_user)
    return SentimentResultResponse(
        sentiment_id=res.sentiment_id,
        feedback_id=res.feedback_id,
        employee_id=res.employee_id if view_emp else None,
        sentiment=res.sentiment,
        sentiment_score=res.sentiment_score,
        model_name=res.model_name,
        model_version=res.model_version,
        analyzed_at=res.analyzed_at
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. DEPARTMENT & TREND ANALYTICS ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/sentiment/department", response_model=DepartmentSentimentResponse)
async def get_department_sentiment(
    current_user: User = Depends(require_hr_analyst)
):
    check_tenant_access(current_user)
    org_id = get_org_id(current_user.organization_id)

    feedbacks = await EmployeeFeedback.find({"organization_id.$id": org_id}).to_list()
    if not feedbacks:
        return DepartmentSentimentResponse(departments=[], total_feedback=0)

    sentiments = await SentimentResult.find({"organization_id.$id": org_id}).to_list()
    sentiments_map = {s.feedback_id: s for s in sentiments}

    items = SentimentAnalysisService.aggregate_department_sentiment(feedbacks, sentiments_map)
    dept_items = [DepartmentSentimentItem(**item) for item in items]

    return DepartmentSentimentResponse(
        departments=dept_items,
        total_feedback=len(feedbacks)
    )


@router.get("/sentiment/trends", response_model=TrendSentimentResponse)
async def get_sentiment_trends(
    department: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: User = Depends(require_hr_analyst)
):
    check_tenant_access(current_user)
    org_id = get_org_id(current_user.organization_id)

    query: Dict[str, Any] = {"organization_id.$id": org_id}
    if department and department.upper() != "ALL":
        query["department"] = department
    if category and category.upper() != "ALL":
        query["category"] = category.upper()

    # Date range filters
    if date_from or date_to:
        date_filter = {}
        if date_from:
            try:
                date_filter["$gte"] = datetime.fromisoformat(date_from)
            except Exception:
                pass
        if date_to:
            try:
                date_filter["$lte"] = datetime.fromisoformat(date_to)
            except Exception:
                pass
        if date_filter:
            query["submitted_at"] = date_filter

    feedbacks = await EmployeeFeedback.find(query).to_list()
    if not feedbacks:
        return TrendSentimentResponse(trends=[], timeframe="monthly")

    # Filter by sentiment if requested
    sentiments = await SentimentResult.find({"organization_id.$id": org_id}).to_list()
    sentiments_map = {s.feedback_id: s for s in sentiments}

    if sentiment and sentiment.upper() != "ALL":
        feedbacks = [f for f in feedbacks if sentiments_map.get(f.feedback_id) and sentiments_map[f.feedback_id].sentiment == sentiment.upper()]

    trend_points = SentimentAnalysisService.aggregate_trends(feedbacks, sentiments_map)
    points = [TrendSentimentPoint(**tp) for tp in trend_points]

    return TrendSentimentResponse(
        trends=points,
        timeframe="monthly"
    )


@router.get("/sentiment/themes", response_model=ThemeAnalysisResponse)
async def get_sentiment_themes(
    department: Optional[str] = Query(None),
    current_user: User = Depends(require_hr_analyst)
):
    check_tenant_access(current_user)
    org_id = get_org_id(current_user.organization_id)

    query: Dict[str, Any] = {"organization_id.$id": org_id}
    if department and department.upper() != "ALL":
        query["department"] = department

    feedbacks = await EmployeeFeedback.find(query).to_list()
    if not feedbacks:
        return ThemeAnalysisResponse(themes=[], total_categorized=0)

    sentiments = await SentimentResult.find({"organization_id.$id": org_id}).to_list()
    sentiments_map = {s.feedback_id: s for s in sentiments}

    extracted = SentimentAnalysisService.extract_themes(feedbacks, sentiments_map)
    theme_items = [ThemeItem(**t) for t in extracted]

    return ThemeAnalysisResponse(
        themes=theme_items,
        total_categorized=len(feedbacks)
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. GROK AI EXECUTIVE INSIGHT ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/sentiment/insight", response_model=AIInsightResponse)
async def generate_sentiment_insight(
    req: AIInsightRequest = AIInsightRequest(),
    current_user: User = Depends(require_hr_analyst)
):
    check_tenant_access(current_user)
    org_id = get_org_id(current_user.organization_id)
    org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
    user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

    query: Dict[str, Any] = {"organization_id.$id": org_id}
    if req.department and req.department.upper() != "ALL":
        query["department"] = req.department

    feedbacks = await EmployeeFeedback.find(query).to_list()
    if not feedbacks:
        return AIInsightResponse(
            insight="No sentiment data available.",
            overall_sentiment={"positive": 0.0, "neutral": 0.0, "negative": 0.0, "total": 0.0},
            top_themes=[],
            department_summary=None,
            generated_at=datetime.now(timezone.utc),
            is_ai_assisted=False
        )

    sentiments = await SentimentResult.find({"organization_id.$id": org_id}).to_list()
    sentiments_map = {s.feedback_id: s for s in sentiments}

    # Calculate overall stats
    total = len(feedbacks)
    pos_count = sum(1 for f in feedbacks if sentiments_map.get(f.feedback_id) and sentiments_map[f.feedback_id].sentiment == "POSITIVE")
    neu_count = sum(1 for f in feedbacks if sentiments_map.get(f.feedback_id) and sentiments_map[f.feedback_id].sentiment == "NEUTRAL")
    neg_count = sum(1 for f in feedbacks if sentiments_map.get(f.feedback_id) and sentiments_map[f.feedback_id].sentiment == "NEGATIVE")

    overall_stats = {
        "positive_pct": round((pos_count / total) * 100, 1),
        "neutral_pct": round((neu_count / total) * 100, 1),
        "negative_pct": round((neg_count / total) * 100, 1),
        "total": float(total)
    }

    themes = SentimentAnalysisService.extract_themes(feedbacks, sentiments_map)
    dept_stats = SentimentAnalysisService.aggregate_department_sentiment(feedbacks, sentiments_map)

    insight_text, is_ai = await SentimentAnalysisService.generate_ai_insight(
        overall_stats=overall_stats,
        top_themes=themes,
        dept_stats=dept_stats,
        department_filter=req.department
    )

    await AuditLog(
        user_id=user_ref,
        organization_id=org_ref,
        action="SENTIMENT_AI_INSIGHT_GENERATED",
        resource_type="SentimentInsight",
        resource_id=req.department or "organization_wide",
        status="SUCCESS"
    ).insert()

    return AIInsightResponse(
        insight=insight_text,
        overall_sentiment={
            "positive": overall_stats["positive_pct"],
            "neutral": overall_stats["neutral_pct"],
            "negative": overall_stats["negative_pct"],
            "total": overall_stats["total"]
        },
        top_themes=[t["theme"] for t in themes[:5]],
        department_summary={"active_departments": len(dept_stats)},
        generated_at=datetime.now(timezone.utc),
        is_ai_assisted=is_ai
    )
