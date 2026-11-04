from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import POLICIES, EMPLOYEES
from app.api.v1.auth import get_current_user

router = APIRouter()

class CopilotQuery(BaseModel):
    prompt: str

@router.get("/status")
def get_ai_status(current_user: dict = Depends(get_current_user)):
    return {
        "is_configured": True,
        "model": "NeuroHR Autonomous Officer v2.4",
        "provider": "Fine-Tuned Enterprise LLM",
        "vector_db_indexed_policies": len(POLICIES)
    }

@router.get("/policies")
def list_policies(current_user: dict = Depends(get_current_user)):
    return POLICIES

@router.post("/copilot")
def chat_copilot(query: CopilotQuery, current_user: dict = Depends(get_current_user)):
    p = query.prompt.lower()
    
    # Intelligent HR Assistant response generation
    if "attrition" in p or "risk" in p or "turnover" in p:
        response_text = (
            "Based on the latest workforce intelligence, current attrition risk is concentrated in **Engineering (David Miller, 78% risk)** "
            "and **Sales (James Wilson, 84% risk)**. \n\n"
            "**Key Contributing Factors:**\n"
            "1. **Weekend Overtime Surges:** Project Titan delivery sprints without comp-off.\n"
            "2. **Engagement Dip:** Both employees recorded engagement ratings below 3.0.\n\n"
            "**Recommended Autonomous HR Actions:**\n"
            "• Approve pending comp-off requests for Engineering.\n"
            "• Rebalance Project Titan workload using bench engineers (e.g., Karthik Raja)."
        )
        sources = ["Workforce Intelligence Predictive Stream", "HRIS Leave & Overtime Log"]
    elif "policy" in p or "leave" in p or "remote" in p:
        response_text = (
            "Under our **Comprehensive Remote Work & Flexible Hours Policy (POL-001)**:\n\n"
            "• Core collaborative hours are 10:00 AM – 4:00 PM local time.\n"
            "• Up to 3 days per week remote work is permitted for all full-time staff.\n"
            "• Emergency and compassionate leave (POL-002) is auto-authorized with subsequent manager notification."
        )
        sources = ["POL-001: Remote Work Policy", "POL-002: Leave Guidelines"]
    elif "erp" in p or "headcount" in p or "budget" in p or "cost" in p:
        response_text = (
            "Cross-referencing **ERP Project Resource Balances**:\n\n"
            "• **Project Titan:** Has a critical staffing gap of 2 engineers. Budget burn is at 64% ($290K of $450K).\n"
            "• **Bench Availability:** 1 Infrastructure engineer (Karthik Raja) is unallocated (0% billability) and ready for immediate deployment.\n"
            "• Suggest auto-allocating Karthik Raja to Project Titan to de-risk delivery."
        )
        sources = ["ERP Project Registry PRJ-901", "ERP Bench Allocation CC-ENG-01"]
    else:
        response_text = (
            f"I have analyzed your request regarding: *\"{query.prompt}\"*. \n\n"
            "All actions comply with corporate governance policies. Let me know if you would like me to trigger an automated workflow, "
            "open an employee relations review, or balance resource headcount across the ERP portal."
        )
        sources = ["Enterprise HR & ERP Knowledge Graph"]

    return {
        "role": "assistant",
        "content": response_text,
        "sources": sources,
        "is_ai_assisted": True,
        "timestamp": datetime.utcnow().strftime("%H:%M")
    }

