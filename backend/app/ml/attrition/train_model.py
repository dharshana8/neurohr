import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

MODEL_PATH = os.path.join(os.path.dirname(__file__), "attrition_model.joblib")

def generate_synthetic_workforce_data(n_samples: int = 2500, random_state: int = 42):
    np.random.seed(random_state)
    
    # Generate realistic features with Indian CTC compensation (in INR)
    # Range ₹8,00,000 to ₹45,00,000
    salary = np.random.normal(2200000, 700000, n_samples).clip(800000, 4500000)
    tenure_years = np.random.exponential(3.5, n_samples).clip(0.5, 15)
    performance = np.random.uniform(2.0, 5.0, n_samples)
    engagement = np.random.uniform(1.5, 5.0, n_samples)
    overtime_hours = np.random.poisson(12, n_samples).clip(0, 50)
    promotions = np.random.choice([0, 1], size=n_samples, p=[0.75, 0.25])
    
    # Ground truth formula calibrated for enterprise HRIS:
    sal_lakhs = salary / 100000.0
    logits = (
        - 0.035 * (sal_lakhs - 22.0)
        - 1.4 * (engagement - 3.5)
        - 0.5 * (performance - 4.0)
        + 0.09 * (overtime_hours - 12.0)
        - 0.5 * promotions
        - 0.8
    )
    probs = 1 / (1 + np.exp(-logits))
    attrition = (np.random.rand(n_samples) < probs).astype(int)

    df = pd.DataFrame({
        "salary": salary,
        "tenure_years": tenure_years,
        "performance": performance,
        "engagement": engagement,
        "overtime_hours": overtime_hours,
        "promotions": promotions,
        "attrition": attrition
    })
    return df

def train_and_save():
    df = generate_synthetic_workforce_data()
    X = df.drop(columns=["attrition"])
    y = df["attrition"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42))
    ])

    pipeline.fit(X_train, y_train)
    accuracy = pipeline.score(X_test, y_test)
    print(f"Model trained successfully. Test Accuracy: {accuracy * 100:.2f}%")

    joblib.dump(pipeline, MODEL_PATH)
    print(f"Serialized model saved to {MODEL_PATH}")
    return pipeline

if __name__ == "__main__":
    train_and_save()
