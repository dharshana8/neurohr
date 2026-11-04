from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
import random
from datetime import datetime

from app.core.database import AI_BENCHMARK_METRICS
from app.api.v1.auth import get_current_user

router = APIRouter()

class ScenarioSimulationRequest(BaseModel):
    category: str
    scenario_prompt: str
    severity: str = "HIGH"

@router.get("/overview")
def get_evaluation_overview(current_user: dict = Depends(get_current_user)):
    return {
        "model_name": AI_BENCHMARK_METRICS["model_name"],
        "overall_hr_competency": AI_BENCHMARK_METRICS["overall_hr_competency"],
        "total_test_cases_run": AI_BENCHMARK_METRICS["total_test_cases_run"],
        "passed_tests": AI_BENCHMARK_METRICS["passed_tests"],
        "failed_tests": AI_BENCHMARK_METRICS["failed_tests"],
        "pass_rate_pct": round((AI_BENCHMARK_METRICS["passed_tests"] / AI_BENCHMARK_METRICS["total_test_cases_run"]) * 100, 1),
        "last_evaluation_timestamp": AI_BENCHMARK_METRICS["last_evaluation_timestamp"],
        "sub_scores": AI_BENCHMARK_METRICS["sub_scores"],
        "scenario_stress_tests": AI_BENCHMARK_METRICS["scenario_stress_tests"]
    }

@router.post("/simulate")
def run_scenario_simulation(req: ScenarioSimulationRequest, current_user: dict = Depends(get_current_user)):
    prompt_lower = req.scenario_prompt.lower()
    
    # Evaluate simulated HR test case dynamically
    if any(k in prompt_lower for k in ["resign", "quit", "offer", "counter", "leave"]):
        verdict = "RETENTION_INTERVENTION_TRIGGERED"
        confidence = 0.94
        reasoning = (
            "Model detected imminent flight risk. Cross-checked employee performance index and ERP project dependency. "
            "Triggered proactive retention protocol rather than standard resignation processing."
        )
        policy_ref = "POL-002 Clause 4.1 (Employee Retention & Succession Guidelines)"
        action_item = "Alert People Business Partner; calculate market compensation adjustment within 4 hours."
    elif any(k in prompt_lower for k in ["harass", "bully", "toxic", "discriminate"]):
        verdict = "CONFIDENTIAL_ESCALATION"
        confidence = 0.99
        reasoning = (
            "Zero-tolerance trigger identified. Sanitized narrative logged in confidential vault. "
            "Prevented any retaliatory management routing. Directed employee to employee care resources."
        )
        policy_ref = "POL-003 Section 2 (Dignity at Work & Anti-Harassment Framework)"
        action_item = "Notify Head of Legal and Chief People Officer via encrypted dispatch."
    elif any(k in prompt_lower for k in ["overtime", "weekend", "tired", "burnout"]):
        verdict = "WORKLOAD_REBALANCING_APPROVED"
        confidence = 0.96
        reasoning = (
            "Cumulative hours analysis confirms sustained excessive overtime (>20 hrs above baseline). "
            "Direct intervention required to prevent attrition and mental fatigue."
        )
        policy_ref = "POL-001 Section 5 (Work-Life Well-being Standard)"
        action_item = "Auto-assign 2 compensatory rest days; rebalance sprint tasks across ERP bench."
    else:
        verdict = "STANDARD_HR_OPERATIONAL_RESOLUTION"
        confidence = 0.92
        reasoning = "Model matched query to internal HR operating standard operating procedure with zero ambiguity."
        policy_ref = "POL-001 (General HR Operating Principles)"
        action_item = "Logged in HRIS audit log."

    result = {
        "simulation_id": f"SIM-{random.randint(1000, 9999)}",
        "category": req.category,
        "scenario_prompt": req.scenario_prompt,
        "severity": req.severity,
        "evaluation_verdict": verdict,
        "confidence_score": confidence,
        "decision_reasoning": reasoning,
        "cited_policy": policy_ref,
        "recommended_action": action_item,
        "latency_ms": random.randint(220, 390),
        "status": "PASSED"
    }

    # Record in history
    AI_BENCHMARK_METRICS["scenario_stress_tests"].insert(0, {
        "id": result["simulation_id"],
        "title": req.scenario_prompt[:45] + ("..." if len(req.scenario_prompt) > 45 else ""),
        "input_prompt": req.scenario_prompt,
        "expected_behavior": f"Fair & Compliant Resolution for {req.category}",
        "ai_decision": f"{verdict}: {action_item}",
        "test_status": "PASSED",
        "latency_ms": result["latency_ms"]
    })
    AI_BENCHMARK_METRICS["total_test_cases_run"] += 1
    AI_BENCHMARK_METRICS["passed_tests"] += 1

    return result

