import os
import joblib
import pandas as pd
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), "attrition_model.joblib")

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

attrition_service = AttritionService()
