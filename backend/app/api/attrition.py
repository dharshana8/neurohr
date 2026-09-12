from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from app.models.user import User
from app.models.employee import Employee
from app.models.attrition import AttritionPrediction
from app.api.deps import get_current_active_user
from app.ml.attrition.service import attrition_service
from app.ml.attrition.shap_explainer import get_shap_explanation

router = APIRouter()

def get_org_id(org_link):
    if hasattr(org_link, "ref"):
        return org_link.ref.id
    if hasattr(org_link, "id"):
        return org_link.id
    return org_link

class SinglePredictionResponse(BaseModel):
    employee_id: str
    probability: float
    risk_score: Optional[float] = None
    risk_level: str
    model_version: str
    prediction_date: datetime
    top_factors: Optional[Dict[str, Any]] = None

class BulkPredictionResponse(BaseModel):
    total: int
    high: int
    medium: int
    low: int

class SummaryResponse(BaseModel):
    total_analyzed: int
    high_risk: int
    medium_risk: int
    low_risk: int

class HighRiskEmployeeItem(BaseModel):
    employee_id: str
    name: str
    department: str
    role: str
    probability: float
    risk_level: str
    prediction_date: datetime

class ExplanationResponse(BaseModel):
    employee_id: str
    probability: float
    risk_level: str
    explanation: Dict[str, Any]

@router.post("/predict/{employee_id}", response_model=SinglePredictionResponse)
async def predict_single(
    employee_id: str,
    current_user: User = Depends(get_current_active_user)
):
    org_id = get_org_id(current_user.organization_id)
    emp = await Employee.find_one(
        {"organization_id.$id": org_id},
        Employee.employee_id == employee_id
    )
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    pred_doc = await attrition_service.predict_single_employee(emp, current_user.organization_id)

    return SinglePredictionResponse(
        employee_id=pred_doc.employee_id,
        probability=pred_doc.probability,
        risk_score=pred_doc.probability,
        risk_level=pred_doc.risk_level,
        model_version=pred_doc.model_version,
        prediction_date=pred_doc.prediction_date,
        top_factors=pred_doc.top_factors
    )

@router.post("/predict-all", response_model=BulkPredictionResponse)
async def predict_all(
    current_user: User = Depends(get_current_active_user)
):
    counts = await attrition_service.predict_bulk(current_user.organization_id)
    return BulkPredictionResponse(
        total=counts["total"],
        high=counts["high"],
        medium=counts["medium"],
        low=counts["low"]
    )

@router.get("/summary", response_model=SummaryResponse)
async def get_summary(current_user: User = Depends(get_current_active_user)):
    org_id = get_org_id(current_user.organization_id)
    preds = await AttritionPrediction.find(
        {"organization_id.$id": org_id}
    ).to_list()
    
    high = sum(1 for p in preds if p.risk_level == "HIGH")
    medium = sum(1 for p in preds if p.risk_level == "MEDIUM")
    low = sum(1 for p in preds if p.risk_level == "LOW")
    
    return SummaryResponse(
        total_analyzed=len(preds),
        high_risk=high,
        medium_risk=medium,
        low_risk=low
    )

@router.get("/high-risk", response_model=List[HighRiskEmployeeItem])
async def get_high_risk(current_user: User = Depends(get_current_active_user)):
    org_id = get_org_id(current_user.organization_id)
    preds = await AttritionPrediction.find(
        {"organization_id.$id": org_id},
        AttritionPrediction.risk_level == "HIGH"
    ).to_list()
    
    results = []
    for p in preds:
        emp = await Employee.find_one(
            {"organization_id.$id": org_id},
            Employee.employee_id == p.employee_id
        )
        if emp:
            results.append(HighRiskEmployeeItem(
                employee_id=emp.employee_id,
                name=emp.name,
                department=emp.department,
                role=emp.role,
                probability=p.probability,
                risk_level=p.risk_level,
                prediction_date=p.prediction_date
            ))
    return results

@router.get("/explain/{employee_id}", response_model=ExplanationResponse)
async def explain_prediction(
    employee_id: str,
    current_user: User = Depends(get_current_active_user)
):
    org_id = get_org_id(current_user.organization_id)
    emp = await Employee.find_one(
        {"organization_id.$id": org_id},
        Employee.employee_id == employee_id
    )
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    pred = await AttritionPrediction.find_one(
        {"organization_id.$id": org_id},
        AttritionPrediction.employee_id == employee_id
    )
    
    if not pred:
        # Generate prediction on the fly
        pred = await attrition_service.predict_single_employee(emp, current_user.organization_id)

    explanation = get_shap_explanation(emp, pred.probability)

    return ExplanationResponse(
        employee_id=emp.employee_id,
        probability=pred.probability,
        risk_level=pred.risk_level,
        explanation=explanation
    )
