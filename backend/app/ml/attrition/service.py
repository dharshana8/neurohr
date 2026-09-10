from datetime import datetime, timezone
from app.models.employee import Employee
from app.models.attrition import AttritionPrediction
from app.ml.attrition.predictor import predictor
from app.ml.attrition.shap_explainer import get_shap_explanation
from app.ml.attrition.preprocessing import preprocess_employee

def get_org_id(org_link):
    if hasattr(org_link, "ref"):
        return org_link.ref.id
    if hasattr(org_link, "id"):
        return org_link.id
    return org_link

class AttritionService:
    async def predict_single_employee(self, employee: Employee, organization_id):
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

