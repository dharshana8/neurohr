import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

def train_and_save_model():
    model_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(model_dir, "attrition_model.joblib")
    
    # Generate synthetic training dataset representing workforce data
    np.random.seed(42)
    n_samples = 300
    
    departments = ["Engineering", "Sales", "HR", "Marketing", "Finance", "Product"]
    roles = ["Software Engineer", "Senior Engineer", "Account Executive", "HR Manager", "Marketing Specialist", "Product Manager"]
    statuses = ["Active", "On Leave"]
    
    data = {
        "department": np.random.choice(departments, n_samples),
        "role": np.random.choice(roles, n_samples),
        "experience": np.round(np.random.uniform(0.5, 15.0, n_samples), 1),
        "salary": np.random.randint(40000, 180000, n_samples),
        "performance_score": np.round(np.random.uniform(1.0, 5.0, n_samples), 1),
        "engagement_score": np.round(np.random.uniform(1.0, 5.0, n_samples), 1),
        "overtime": np.random.randint(0, 30, n_samples),
        "promotion_history": np.random.choice([0, 1, 2, 3], n_samples, p=[0.6, 0.25, 0.1, 0.05]),
        "employment_status": np.random.choice(statuses, n_samples, p=[0.9, 0.1])
    }
    
    df = pd.DataFrame(data)
    
    # Target rule: low engagement, high overtime, low performance -> higher attrition risk
    attrition_prob = (
        (5.0 - df["engagement_score"]) * 0.15 +
        (df["overtime"] / 30.0) * 0.25 +
        (5.0 - df["performance_score"]) * 0.15 +
        (df["experience"] > 4.0) * (df["promotion_history"] == 0) * 0.2
    )
    attrition_target = (attrition_prob > 0.45).astype(int)
    
    num_features = ["experience", "salary", "performance_score", "engagement_score", "overtime", "promotion_history"]
    cat_features = ["department", "role", "employment_status"]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_features)
        ]
    )
    
    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(n_estimators=100, random_state=42, max_depth=8, class_weight="balanced"))
    ])
    
    pipeline.fit(df, attrition_target)
    
    joblib.dump(pipeline, model_path)
    print(f"Successfully trained and saved attrition model to {model_path}")
    return pipeline

if __name__ == "__main__":
    train_and_save_model()
