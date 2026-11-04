"""
NeuroHR X - Attrition Prediction Machine Learning Model Test & Audit Script
Run this script to test the model with any custom employee parameters.
"""

import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.ml.attrition.service import attrition_service

def test_custom_scenario(name: str, salary_inr: float, engagement: float, overtime_hours: float, performance: float = 4.0, tenure: float = 3.0, promotions: int = 0):
    print("=" * 70)
    print(f">> Testing Scenario: {name}")
    print(f"   * Annual Salary: INR {salary_inr:,.0f} ({salary_inr/100000:.1f} Lakhs)")
    print(f"   * Engagement Score: {engagement:.1f} / 5.0")
    print(f"   * Overtime Worked: {overtime_hours:.0f} hrs / month")
    print(f"   * Performance Rating: {performance:.1f} / 5.0")
    print(f"   * Company Tenure: {tenure:.1f} years | Promotions: {promotions}")
    print("-" * 70)

    result = attrition_service.predict_risk(
        salary=salary_inr,
        tenure_years=tenure,
        performance=performance,
        engagement=engagement,
        overtime_hours=overtime_hours,
        promotions=promotions
    )

    prob = result["attrition_probability"]
    level = result["risk_level"]
    drivers = result["top_drivers"]

    badge = "[HIGH FLIGHT RISK]" if level == "HIGH" else "[MEDIUM ATTENTION]" if level == "MEDIUM" else "[LOW RETENTION RISK]"

    print(f"Model Prediction Result:")
    print(f"   * Flight Risk Probability: {int(prob * 100)}% ({prob})")
    print(f"   * Risk Classification:    {badge}")
    print(f"   * Top Model Drivers:")
    for d in drivers:
        print(f"     -> {d}")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    print("\n--- Starting NeuroHR Attrition ML Diagnostics Suite ---\n")

    # Scenario 1: Severe Burnout & Low Engagement (Expected: HIGH RISK)
    test_custom_scenario(
        name="Severe Burnout Engineer (e.g. David Miller)",
        salary_inr=2400000,
        engagement=2.1,
        overtime_hours=38,
        performance=3.9,
        tenure=3.8,
        promotions=0
    )

    # Scenario 2: Stressed Account Executive (Expected: HIGH RISK)
    test_custom_scenario(
        name="Stressed Account Executive (e.g. James Wilson)",
        salary_inr=2200000,
        engagement=2.0,
        overtime_hours=35,
        performance=3.4,
        tenure=3.1,
        promotions=0
    )

    # Scenario 3: Moderate Workload Crunch (Expected: MEDIUM RISK)
    test_custom_scenario(
        name="Moderate Crunch Backend Engineer (e.g. Karthik Raja)",
        salary_inr=2200000,
        engagement=3.2,
        overtime_hours=22,
        performance=4.2,
        tenure=3.1,
        promotions=0
    )

    # Scenario 4: Highly Engaged Top Performer (Expected: LOW RISK)
    test_custom_scenario(
        name="Happy Principal Architect (e.g. Sarah Connor)",
        salary_inr=3850000,
        engagement=4.5,
        overtime_hours=8,
        performance=4.8,
        tenure=4.2,
        promotions=1
    )

    # Scenario 5: High Salary but Extreme Overtime
    test_custom_scenario(
        name="Well-Paid but Fatigued Staff ML Engineer",
        salary_inr=3500000,
        engagement=2.8,
        overtime_hours=36,
        performance=4.7,
        tenure=2.4,
        promotions=0
    )
