import shap
import pandas as pd
import numpy as np
from app.ml.attrition.model_loader import model_loader
from app.ml.attrition.preprocessing import preprocess_employee

FEATURE_DESCRIPTIONS = {
    "engagement_score": "Engagement Score",
    "overtime": "Weekly Overtime Hours",
    "performance_score": "Performance Score",
    "promotion_history": "Promotion History",
    "experience": "Years of Experience",
    "salary": "Compensation / Salary",
    "department": "Department Context",
    "role": "Role Profile",
    "employment_status": "Employment Status"
}

def get_shap_explanation(employee, probability: float):
    """
    Computes real SHAP feature importances using tree explainer on the trained Random Forest model.
    """
    try:
        pipeline = model_loader.get_model()
        classifier = pipeline.named_steps["classifier"]
        preprocessor = pipeline.named_steps["preprocessor"]
        
        df = preprocess_employee(employee)
        X_trans = preprocessor.transform(df)
        
        feature_names = list(preprocessor.get_feature_names_out())
        
        explainer = shap.TreeExplainer(classifier)
        shap_values = explainer.shap_values(X_trans)
        
        # Binary classification shap values handling
        if isinstance(shap_values, list):
            sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        elif hasattr(shap_values, "values") and len(shap_values.values.shape) == 3:
            sv = shap_values.values[0, :, 1]
        elif hasattr(shap_values, "values"):
            sv = shap_values.values[0]
        else:
            sv = shap_values[0]
            
        # Aggregate one-hot encoded feature importances back to raw feature categories
        feature_impacts = {}
        for name, val in zip(feature_names, sv):
            # Extract base feature name (e.g. num__engagement_score -> engagement_score)
            base_name = name.split("__")[-1].split("_")[0] if "__" in name else name
            for key in FEATURE_DESCRIPTIONS.keys():
                if key in name:
                    base_name = key
                    break
            feature_impacts[base_name] = feature_impacts.get(base_name, 0.0) + float(val)
            
        sorted_factors = sorted(feature_impacts.items(), key=lambda x: abs(x[1]), reverse=True)
        
        top_factors = []
        for feat, val in sorted_factors[:4]:
            impact_type = "negative" if (val > 0 and probability >= 0.3) else "positive"
            desc = FEATURE_DESCRIPTIONS.get(feat, feat.replace("_", " ").title())
            top_factors.append({
                "feature": feat,
                "impact": impact_type,
                "shap_value": round(val, 4),
                "description": f"{desc} (Impact: {'High Attrition Contributor' if val > 0 else 'Retention Booster'})"
            })
            
        return {
            "available": True,
            "top_factors": top_factors
        }
    except Exception as e:
        return {
            "available": False,
            "error": f"Explanation unavailable: {str(e)}",
            "top_factors": []
        }
