import numpy as np
from app.ml.attrition.model_loader import model_loader
from app.ml.attrition.preprocessing import preprocess_employee

class AttritionPredictor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AttritionPredictor, cls).__new__(cls)
        return cls._instance

    def predict(self, employee):
        df = preprocess_employee(employee)
        pipeline = model_loader.get_model()
        
        # Calculate probability of attrition (class 1)
        proba_array = pipeline.predict_proba(df)[0]
        # Class 1 probability
        probability = float(proba_array[1]) if len(proba_array) > 1 else float(proba_array[0])
        probability = round(probability, 4)

        if probability < 0.30:
            risk_level = "LOW"
        elif probability < 0.70:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        return probability, risk_level

predictor = AttritionPredictor()
