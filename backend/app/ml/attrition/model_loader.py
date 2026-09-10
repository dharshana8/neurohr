import os
import joblib

class ModelLoader:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
        return cls._instance

    def get_model(self):
        if self._model is None:
            model_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(model_dir, "attrition_model.joblib")
            
            if not os.path.exists(model_path):
                from app.ml.attrition.train_model import train_and_save_model
                self._model = train_and_save_model()
            else:
                self._model = joblib.load(model_path)
                
        return self._model

model_loader = ModelLoader()
