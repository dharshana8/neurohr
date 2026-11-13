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
    overtime_hours = np.random.exponential(12, n_samples).clip(0, 55)
    promotions = np.random.poisson(0.8, n_samples).clip(0, 5)

    # Realistic attrition probability formula (ground truth generation)
    # High overtime + low engagement + low salary relative to tenure = high flight risk
    salary_factor = -0.04 * ((salary - 2200000) / 100000.0)
    engagement_factor = -1.6 * (engagement - 3.2)
    perf_factor = -0.4 * (performance - 3.8)
    overtime_factor = 0.12 * (overtime_hours - 10)
    stagnation_factor = 0.35 * (tenure_years - (promotions * 2.5 + 1.0))

    logits = salary_factor + engagement_factor + perf_factor + overtime_factor + stagnation_factor - 1.1
    probs = 1 / (1 + np.exp(-logits))
    attrition = (np.random.uniform(0, 1, n_samples) < probs).astype(int)

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
    print("Generating synthetic enterprise INR workforce training data...")
    df = generate_synthetic_workforce_data(n_samples=3000)

    X = df[["salary", "tenure_years", "performance", "engagement", "overtime_hours", "promotions"]]
    y = df["attrition"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", RandomForestClassifier(
            n_estimators=120,
            max_depth=6,
            min_samples_split=4,
            random_state=42,
            class_weight="balanced"
        ))
    ])

    pipeline.fit(X_train, y_train)
    accuracy = pipeline.score(X_test, y_test)
    print(f"Model trained successfully. Test Accuracy: {accuracy * 100:.2f}%")

    joblib.dump(pipeline, MODEL_PATH)
    print(f"Serialized model saved to {MODEL_PATH}")
    return pipeline

if __name__ == "__main__":
    train_and_save()
