import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timezone

MODEL_PATH = os.path.join(os.path.dirname(__file__), "attrition_model.joblib")

def get_org_id(org_link):
    if hasattr(org_link, "ref"):
        return org_link.ref.id
    if hasattr(org_link, "id"):
        return org_link.id
    return org_link

class AttritionService:
    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"Error loading model: {e}")
                self.model = None

    def predict_risk(self, salary: float, tenure_years: float, performance: float, engagement: float, overtime_hours: float = 10, promotions: int = 0):
        # Auto-detect USD vs INR: if salary < 300,000, it's USD, scale to INR equivalent
        sal_inr = salary * 25.0 if salary < 300000 else salary

        if self.model is None:
            self._load_model()

        if self.model is not None:
            try:
                X = pd.DataFrame([{
                    "salary": float(sal_inr),
                    "tenure_years": float(tenure_years),
                    "performance": float(performance),
                    "engagement": float(engagement),
                    "overtime_hours": float(overtime_hours),
                    "promotions": int(promotions)
                }])
                prob = float(self.model.predict_proba(X)[0][1])
            except Exception as ex:
                print(f"Model prediction failed, using fallback formula: {ex}")
                prob = None
        else:
            prob = None

        if prob is None:
            # Calibrated formula fallback
            sal_lakhs = sal_inr / 100000.0
            logits = (
                - 0.035 * (sal_lakhs - 22.0)
                - 1.4 * (engagement - 3.5)
                - 0.5 * (performance - 4.0)
                + 0.09 * (overtime_hours - 12.0)
                - 0.5 * promotions
                - 0.8
            )
            prob = float(1 / (1 + np.exp(-logits)))

        prob = max(0.04, min(0.96, prob))
        level = "HIGH" if prob >= 0.65 else "MEDIUM" if prob >= 0.35 else "LOW"

        # Key drivers based on employee stats
        drivers = []
        if engagement < 3.0:
            drivers.append("Low Workplace Engagement Score (< 3.0/5.0)")
        if overtime_hours > 20:
            drivers.append(f"Excessive Sprint Overtime Crunch ({int(overtime_hours)} hrs/mo)")
        if sal_inr < 1800000:
            drivers.append("Compensation Below Market Median Band")
        if tenure_years > 3 and promotions == 0:
            drivers.append("Tenure Stagnation Without Milestone Promotion")
        if not drivers:
            drivers = ["Stable Retention Outlook", "Healthy Work-Life Balance"]

        return {
            "attrition_probability": round(prob, 2),
            "risk_level": level,
            "top_drivers": drivers
        }

    async def predict_single_employee(self, employee, organization_id):
        from app.models.attrition import AttritionPrediction
        from app.ml.attrition.predictor import predictor
        from app.ml.attrition.shap_explainer import get_shap_explanation
        from app.ml.attrition.preprocessing import preprocess_employee

        probability, risk_level = predictor.predict(employee)
        explanation = get_shap_explanation(employee, probability)
        features_used = preprocess_employee(employee).to_dict(orient="records")[0]

        org_id = get_org_id(organization_id)

        existing = await AttritionPrediction.find_one(
            {"organization_id.$id": org_id},
            AttritionPrediction.employee_id == employee.employee_id
        )

        org_ref = organization_id.to_ref() if hasattr(organization_id, "to_ref") else organization_id
        if existing:
            existing.probability = probability
            existing.risk_level = risk_level
            existing.model_version = "demo-v1"
            existing.top_factors = explanation
            existing.features_used = features_used
            existing.prediction_date = datetime.now(timezone.utc)
            await existing.save()
            prediction_doc = existing
        else:
            prediction_doc = AttritionPrediction(
                organization_id=org_ref,
                employee_id=employee.employee_id,
                probability=probability,
                risk_level=risk_level,
                model_version="demo-v1",
                top_factors=explanation,
                features_used=features_used
            )
            await prediction_doc.insert()

        return prediction_doc

    async def predict_bulk(self, organization_id):
        from app.models.employee import Employee
        org_id = get_org_id(organization_id)
        employees = await Employee.find({"organization_id.$id": org_id}).to_list()

        counts = {"total": len(employees), "high": 0, "medium": 0, "low": 0}
        
        for emp in employees:
            pred_doc = await self.predict_single_employee(emp, organization_id)
            level = pred_doc.risk_level.lower()
            if level in counts:
                counts[level] += 1

        return counts

attrition_service = AttritionService()
