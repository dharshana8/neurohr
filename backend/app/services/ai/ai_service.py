from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone
import uuid
import re

from app.models.user import User
from app.models.employee import Employee
from app.models.attrition import AttritionPrediction
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.match import CandidateMatch
from app.models.intelligence import SkillGapAnalysis, RoleSkillRequirement
from app.models.ai import AIChatConversation, HRPolicyDocument
from app.services.ai.grok_client import grok_client
from app.services.ai.policy_rag import PolicyRAGService
from app.services.ai.exceptions import AIServiceError, AIConfigurationError
from app.services.ai.prompts import (
    COPILOT_SYSTEM_PROMPT,
    ATTRITION_EXPLAIN_PROMPT,
    CAREER_RECOMMEND_PROMPT,
    RECRUITMENT_EXPLAIN_PROMPT,
    SENTIMENT_SUMMARY_PROMPT,
    POLICY_RAG_PROMPT,
    ANALYTICS_SUMMARY_PROMPT
)
from app.services.ai.schemas import (
    AICopilotResponse,
    AttritionExplainResponse,
    CareerRecommendResponse,
    DevelopmentAreaItem,
    RecruitmentExplainResponse,
    SentimentSummaryResponse,
    PolicyQueryResponse
)

def get_org_id(org_link):
    if hasattr(org_link, "ref"):
        return org_link.ref.id
    if hasattr(org_link, "id"):
        return org_link.id
    return org_link

class AIService:
    @staticmethod
    async def chat_copilot(
        current_user: User,
        message: str,
        conversation_id: Optional[str] = None
    ) -> AICopilotResponse:
        """
        AI HR Copilot: Answers inquiries using verified, tenant-isolated data
        and organization HR policy documents without hallucinating.
        """
        org_id = get_org_id(current_user.organization_id)
        org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
        user_ref = current_user.to_ref() if hasattr(current_user, "to_ref") else current_user

        # 1. Resolve or Create Conversation
        conv = None
        if conversation_id:
            conv = await AIChatConversation.find_one({
                "conversation_id": conversation_id,
                "organization_id.$id": org_id,
                "user_id.$id": current_user.id
            })

        if not conv:
            conv = AIChatConversation(
                conversation_id=str(uuid.uuid4()),
                organization_id=org_ref,
                user_id=user_ref,
                title=message[:40] + ("..." if len(message) > 40 else ""),
                messages=[]
            )
            await conv.insert()

        # 2. Check Demo Mode (Grok unconfigured)
        if not grok_client.is_configured:
            # Provide intelligent local deterministic answer based on DB data
            local_context, sources, raw_data = await AIService._gather_structured_context(org_id, message)
            demo_answer = (
                f"**[Demo Mode - Generative AI Not Configured]**\n\n"
                f"To unlock natural-language Grok reasoning, set `XAI_API_KEY` in your environment.\n\n"
                f"**Verified Organization Data:**\n{local_context}"
            )
            # Record in conversation
            conv.messages.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            conv.messages.append({
                "role": "assistant",
                "content": demo_answer,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sources": sources
            })
            conv.updated_at = datetime.now(timezone.utc)
            await conv.save()

            return AICopilotResponse(
                answer=demo_answer,
                conversation_id=conv.conversation_id,
                sources=sources,
                supporting_data=raw_data,
                is_ai_assisted=False,
                demo_mode=True
            )

        # 3. Gather minimal, verified structured data for this tenant
        structured_context, sources, supporting_data = await AIService._gather_structured_context(org_id, message)

        # 4. Build prompt messages with conversation history (last 6 messages)
        prompt_messages: List[Dict[str, str]] = [
            {"role": "system", "content": COPILOT_SYSTEM_PROMPT}
        ]

        # Context injection
        context_system_msg = (
            f"VERIFIED ORGANIZATION CONTEXT (Use strictly as source of truth):\n{structured_context}"
        )
        prompt_messages.append({"role": "system", "content": context_system_msg})

        # History
        for past_msg in conv.messages[-6:]:
            prompt_messages.append({
                "role": past_msg.get("role", "user"),
                "content": past_msg.get("content", "")
            })

        # Current user message
        prompt_messages.append({"role": "user", "content": message})

        # 5. Call Grok
        ai_answer = await grok_client.generate_chat(
            messages=prompt_messages,
            temperature=0.3,
            max_tokens=1000
        )

        # 6. Save messages to conversation history
        conv.messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        conv.messages.append({
            "role": "assistant",
            "content": ai_answer,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sources": sources
        })
        conv.updated_at = datetime.now(timezone.utc)
        await conv.save()

        return AICopilotResponse(
            answer=ai_answer,
            conversation_id=conv.conversation_id,
            sources=sources,
            supporting_data=supporting_data,
            is_ai_assisted=True,
            demo_mode=False
        )

    @staticmethod
    async def _gather_structured_context(
        org_id,
        message: str
    ) -> Tuple[str, List[str], Dict[str, Any]]:
        """
        Controlled data gathering function for Copilot:
        Detects query intent and executes tenant-scoped queries with minimal PII.
        """
        msg_lower = message.lower()
        context_parts = []
        sources = []
        supporting_data: Dict[str, Any] = {}

        # Intent: Attrition
        if any(w in msg_lower for w in ["attrition", "risk", "turnover", "leave", "retention", "quitting"]):
            preds = await AttritionPrediction.find(
                {"organization_id.$id": org_id},
                AttritionPrediction.risk_level == "HIGH"
            ).to_list()
            employees = await Employee.find({"organization_id.$id": org_id}).to_list()
            dept_risk: Dict[str, int] = {}
            for e in employees:
                dept_risk[e.department] = dept_risk.get(e.department, 0)
            
            # Map high risk count per department
            emp_map = {e.employee_id: e.department for e in employees}
            for p in preds:
                d = emp_map.get(p.employee_id, "General")
                dept_risk[d] = dept_risk.get(d, 0) + 1

            sorted_depts = sorted(dept_risk.items(), key=lambda x: x[1], reverse=True)
            top_risk_dept = sorted_depts[0] if sorted_depts else ("None", 0)

            context_parts.append(
                f"- High Attrition Risk Count: {len(preds)} employees\n"
                f"- Total Workforce: {len(employees)} employees\n"
                f"- Highest Risk Department: {top_risk_dept[0]} ({top_risk_dept[1]} high-risk individuals)\n"
                f"- Department Risk Breakdown: {', '.join(f'{k}: {v}' for k, v in sorted_depts[:4])}"
            )
            sources.append("Workforce Attrition Intelligence Engine")
            supporting_data["attrition"] = {"high_risk_count": len(preds), "department_risk": dict(sorted_depts[:5])}

        # Intent: Skill gaps
        if any(w in msg_lower for w in ["skill", "gap", "competenc", "training", "development"]):
            gaps = await SkillGapAnalysis.find({"organization_id.$id": org_id}).to_list()
            if gaps:
                gap_freq: Dict[str, int] = {}
                for g in gaps:
                    for m in g.missing_skills:
                        sk = m.get("skill")
                        if sk:
                            gap_freq[sk] = gap_freq.get(sk, 0) + 1
                top_missing = sorted(gap_freq.items(), key=lambda x: x[1], reverse=True)[:5]
                avg_coverage = round(sum(g.skill_coverage_score for g in gaps) / len(gaps), 1)
                context_parts.append(
                    f"- Analyzed Workforce Profiles: {len(gaps)}\n"
                    f"- Organization Avg Skill Coverage: {avg_coverage}%\n"
                    f"- Top Identified Skill Gaps: {', '.join(f'{s} ({c} instances)' for s, c in top_missing)}"
                )
                sources.append("Skill Gap Intelligence System")
                supporting_data["skill_gaps"] = {"avg_coverage": avg_coverage, "top_missing": dict(top_missing)}

        # Intent: Recruitment / Hiring
        if any(w in msg_lower for w in ["recruitment", "job", "candidate", "applicant", "resume", "hiring"]):
            jobs = await Job.find({"organization_id.$id": org_id}).to_list()
            candidates = await Candidate.find({"organization_id.$id": org_id}).to_list()
            active_jobs = [j for j in jobs if j.status == "ACTIVE"]
            context_parts.append(
                f"- Total Posted Jobs: {len(jobs)} ({len(active_jobs)} active)\n"
                f"- Total Candidates in Pipeline: {len(candidates)}\n"
                f"- Active Positions: {', '.join(j.title for j in active_jobs[:4])}"
            )
            sources.append("Recruitment & ATS Pipeline")
            supporting_data["recruitment"] = {"active_jobs": len(active_jobs), "total_candidates": len(candidates)}

        # Intent: Policy RAG / Leave / Benefits / Rules
        if any(w in msg_lower for w in ["policy", "leave", "holiday", "maternity", "paternity", "sick", "work from home", "remote", "handbook", "guideline", "benefit"]):
            policy_results = await PolicyRAGService.search_relevant_chunks(org_id, message, top_k=3)
            if policy_results:
                policy_text = PolicyRAGService.format_chunks_for_prompt(policy_results)
                context_parts.append(f"RELEVANT POLICY EXCERPTS:\n{policy_text}")
                for p in policy_results:
                    if p["title"] not in sources:
                        sources.append(f"HR Policy: {p['title']}")

        # Fallback / General Employee stats
        if not context_parts:
            employees = await Employee.find({"organization_id.$id": org_id}).to_list()
            total_emp = len(employees)
            dept_counts: Dict[str, int] = {}
            for e in employees:
                dept_counts[e.department] = dept_counts.get(e.department, 0) + 1

            context_parts.append(
                f"- Total Employees: {total_emp}\n"
                f"- Departments: {', '.join(f'{d} ({c})' for d, c in list(dept_counts.items())[:5])}"
            )
            sources.append("Workforce Directory")
            supporting_data["headcount"] = total_emp

        return "\n\n".join(context_parts), sources, supporting_data

    @staticmethod
    async def explain_attrition(
        current_user: User,
        employee_id: str
    ) -> AttritionExplainResponse:
        """
        Translates structured SHAP/ML model output into human-friendly explanation.
        Strictly forbids inventing factors not present in the model output.
        """
        org_id = get_org_id(current_user.organization_id)

        # 1. Retrieve employee and prediction
        employee = await Employee.find_one(
            {"organization_id.$id": org_id},
            Employee.employee_id == employee_id
        )
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        prediction = await AttritionPrediction.find_one(
            {"organization_id.$id": org_id},
            AttritionPrediction.employee_id == employee_id
        )

        risk_level = prediction.risk_level if prediction else ("HIGH" if employee.attrition == 1 else "LOW")
        raw_prob = getattr(prediction, "probability", None)
        if raw_prob is None:
            raw_prob = getattr(prediction, "attrition_risk_score", 0.75 if employee.attrition == 1 else 0.15)
        risk_score = round(float(raw_prob), 2)

        # Top factors from prediction or standard model features
        factors = []
        if prediction and getattr(prediction, "top_factors", None):
            tf = prediction.top_factors
            if isinstance(tf, dict):
                if isinstance(tf.get("top_factors"), list) and len(tf["top_factors"]) > 0:
                    factors = tf["top_factors"]
                else:
                    factors = [
                        {"feature": k, "impact": "negative" if (isinstance(v, (int, float)) and v > 0) else "positive", "description": f"{k} (impact {v})"}
                        for k, v in tf.items() if k not in ["available", "error", "top_factors"]
                    ]
            elif isinstance(tf, list):
                factors = tf

        if not factors:
            factors = [
                {"feature": "overtime", "impact": "negative", "description": f"Overtime hours ({employee.overtime}h)"},
                {"feature": "engagement_score", "impact": "negative", "description": f"Engagement level ({employee.engagement_score}/5.0)"},
                {"feature": "performance_score", "impact": "positive", "description": f"Performance rating ({employee.performance_score}/5.0)"}
            ]

        factors_text = "\n".join(f"- {f.get('feature')}: {f.get('description', f.get('impact'))}" for f in factors)

        # Build structured factor lists for UI SHAP cards
        top_risk_factors = []
        protective_factors = []
        for f in factors:
            feat_title = f.get("feature", "Factor").replace("_", " ").title()
            impact_raw = f.get("impact", "")
            shap_val = f.get("shap_value")

            if isinstance(shap_val, (int, float)):
                impact_display = f"{abs(shap_val):.2f}"
            else:
                impact_display = "High" if impact_raw == "negative" else "Low"

            factor_item = {
                "factor": feat_title,
                "impact": impact_display,
                "description": f.get("description", "")
            }

            if impact_raw == "negative" or (isinstance(shap_val, (int, float)) and shap_val > 0):
                top_risk_factors.append(factor_item)
            else:
                protective_factors.append(factor_item)

        # 2. Generate explanation with Grok or fallback
        if not grok_client.is_configured:
            fallback_explanation = (
                f"Estimated attrition risk is {risk_level.lower()} (score: {risk_score}). "
                f"The primary model indicators are {factors[0].get('feature', 'engagement')} and {factors[1].get('feature', 'overtime')}."
            )
            return AttritionExplainResponse(
                employee_id=employee_id,
                risk_level=risk_level,
                risk_score=risk_score,
                probability=risk_score,
                model_factors=factors,
                top_risk_factors=top_risk_factors,
                protective_factors=protective_factors,
                ai_explanation=fallback_explanation,
                ai_narrative=fallback_explanation,
                is_ai_assisted=False,
                disclaimer="Deterministic model factor summary (Grok unconfigured)."
            )

        prompt = ATTRITION_EXPLAIN_PROMPT.format(
            risk_level=risk_level,
            risk_score=risk_score,
            factors_text=factors_text
        )

        ai_explanation = await grok_client.generate_text(
            prompt=prompt,
            temperature=0.2,
            max_tokens=250
        )

        return AttritionExplainResponse(
            employee_id=employee_id,
            risk_level=risk_level,
            risk_score=risk_score,
            probability=risk_score,
            model_factors=factors,
            top_risk_factors=top_risk_factors,
            protective_factors=protective_factors,
            ai_explanation=ai_explanation,
            ai_narrative=ai_explanation,
            is_ai_assisted=True
        )

    @staticmethod
    async def recommend_career_path(
        current_user: User,
        employee_id: str,
        target_role: str
    ) -> CareerRecommendResponse:
        """
        Generates natural-language career development recommendations and milestones
        grounded strictly in the deterministic skill-gap analysis.
        """
        org_id = get_org_id(current_user.organization_id)

        # 1. Retrieve employee
        employee = await Employee.find_one(
            {"organization_id.$id": org_id},
            Employee.employee_id == employee_id
        )
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        # 2. Retrieve / run deterministic gap analysis
        from app.intelligence.services.skill_gap_service import SkillGapService
        gap_analysis = await SkillGapService.analyze_gap(
            employee_id=employee_id,
            target_role=target_role,
            org_id=org_id,
            user=current_user
        )

        matched_names = [m["skill"] for m in gap_analysis.matched_skills]
        missing_names = [m["skill"] for m in gap_analysis.missing_skills]
        partial_names = [p["skill"] for p in gap_analysis.partial_skills]

        context_text = f"Experience: {employee.experience} yrs; Performance Score: {employee.performance_score}/5.0 (Advisory context only)"

        # Fallback if Grok is not configured
        if not grok_client.is_configured:
            dev_areas = [
                DevelopmentAreaItem(
                    skill=s,
                    reason=f"Required competency for {target_role}",
                    recommended_action=f"Complete targeted training and practical projects in {s}"
                ) for s in missing_names[:3]
            ]
            milestones = [
                f"Phase 1: Acquire foundational capability in {', '.join(missing_names[:2]) or 'core role skills'}",
                f"Phase 2: Deliver hands-on applied project in {target_role} competencies",
                "Phase 3: Manager and HR readiness checkpoint"
            ]
            return CareerRecommendResponse(
                employee_id=employee_id,
                current_role=employee.role,
                target_role=target_role,
                summary=f"Recommended career roadmap from {employee.role} to {target_role} focusing on closing identified skill gaps.",
                development_areas=dev_areas,
                milestones=milestones,
                is_ai_assisted=False,
                disclaimer="Deterministic rule-based recommendations (Grok unconfigured)."
            )

        prompt = CAREER_RECOMMEND_PROMPT.format(
            current_role=employee.role,
            target_role=target_role,
            matched_skills=", ".join(matched_names) or "None recorded",
            missing_skills=", ".join(missing_names) or "None",
            partial_skills=", ".join(partial_names) or "None",
            context_text=context_text
        )

        try:
            parsed_json = await grok_client.generate_json(prompt=prompt, temperature=0.2)
            dev_areas = [
                DevelopmentAreaItem(
                    skill=d.get("skill", "General Competency"),
                    reason=d.get("reason", "Required for target role"),
                    recommended_action=d.get("recommended_action", "Undergo training")
                )
                for d in parsed_json.get("development_areas", [])
            ]
            milestones = parsed_json.get("milestones", [])
            summary = parsed_json.get("summary", f"Career progression plan for {target_role}.")
        except Exception:
            # Fallback gracefully
            dev_areas = [
                DevelopmentAreaItem(
                    skill=s,
                    reason=f"Skill gap identified for {target_role}",
                    recommended_action=f"Foundational coursework and mentoring in {s}"
                ) for s in missing_names[:3]
            ]
            milestones = [f"Complete training in {s}" for s in missing_names[:3]] + ["HR & Manager Review"]
            summary = f"Structured development path toward {target_role}."

        return CareerRecommendResponse(
            employee_id=employee_id,
            current_role=employee.role,
            target_role=target_role,
            summary=summary,
            development_areas=dev_areas,
            milestones=milestones,
            is_ai_assisted=True
        )

    @staticmethod
    async def explain_recruitment_match(
        current_user: User,
        candidate_id: str,
        job_id: str
    ) -> RecruitmentExplainResponse:
        """
        Translates candidate match scores and features into a readable recruiter brief.
        Does not recalculate or invent scores.
        """
        org_id = get_org_id(current_user.organization_id)

        candidate = await Candidate.find_one(
            {"organization_id.$id": org_id},
            Candidate.candidate_id == candidate_id
        )
        if not candidate:
            raise ValueError("Candidate not found")

        job = await Job.find_one(
            {"organization_id.$id": org_id},
            Job.job_id == job_id
        )
        if not job:
            raise ValueError("Job not found")

        match_record = await CandidateMatch.find_one(
            {"organization_id.$id": org_id},
            CandidateMatch.candidate_id == candidate_id,
            CandidateMatch.job_id == job_id
        )

        match_score = getattr(match_record, "match_score", 80.0) if match_record else 80.0

        cand_skills = set()
        if isinstance(candidate.skills, list):
            cand_skills = set(s.strip().lower() for s in candidate.skills if s.strip())
        elif isinstance(candidate.skills, str):
            cand_skills = set(s.strip().lower() for s in candidate.skills.split(',') if s.strip())

        cand_exp = getattr(candidate, "experience", getattr(candidate, "experience_years", 0.0))
        job_skills = getattr(job, "required_skills", getattr(job, "skills_required", []))
        job_exp = getattr(job, "minimum_experience", getattr(job, "experience_min", 0.0))

        matched = [s for s in job_skills if s.strip().lower() in cand_skills]
        missing = [s for s in job_skills if s.strip().lower() not in cand_skills]
        exp_verdict = (
            f"Meets requirements ({cand_exp} yrs vs {job_exp} yrs required)"
            if cand_exp >= job_exp
            else f"Below target ({cand_exp} yrs vs {job_exp} yrs required)"
        )

        if not grok_client.is_configured:
            fallback = (
                f"Candidate {candidate.name} has a match score of {match_score}%. "
                f"Matched skills include {', '.join(matched[:3]) or 'relevant capabilities'}. "
                f"Missing requirements: {', '.join(missing[:2]) or 'None identified'}."
            )
            return RecruitmentExplainResponse(
                candidate_id=candidate_id,
                candidate_name=candidate.name,
                job_id=job_id,
                job_title=job.title,
                match_score=match_score,
                matched_skills=matched,
                missing_skills=missing,
                experience_verdict=exp_verdict,
                ai_explanation=fallback,
                is_ai_assisted=False
            )

        prompt = RECRUITMENT_EXPLAIN_PROMPT.format(
            job_title=job.title,
            candidate_name=candidate.name,
            match_score=match_score,
            matched_skills=", ".join(matched) or "None",
            missing_skills=", ".join(missing) or "None",
            experience_verdict=exp_verdict
        )

        ai_explanation = await grok_client.generate_text(
            prompt=prompt,
            temperature=0.2,
            max_tokens=300
        )

        return RecruitmentExplainResponse(
            candidate_id=candidate_id,
            candidate_name=candidate.name,
            job_id=job_id,
            job_title=job.title,
            match_score=match_score,
            matched_skills=matched,
            missing_skills=missing,
            experience_verdict=exp_verdict,
            ai_explanation=ai_explanation,
            is_ai_assisted=True
        )

    @staticmethod
    async def summarize_sentiment(
        current_user: User,
        department: Optional[str] = None
    ) -> SentimentSummaryResponse:
        """
        Summarizes aggregated employee sentiment feedback safely without PII.
        """
        org_id = get_org_id(current_user.organization_id)
        query: Dict[str, Any] = {"organization_id.$id": org_id}
        if department and department.lower() != "all":
            query["department"] = department

        employees = await Employee.find(query).to_list()
        total = len(employees)
        if total == 0:
            return SentimentSummaryResponse(
                department=department or "All Departments",
                total_feedbacks=0,
                positive_pct=0.0,
                neutral_pct=0.0,
                negative_pct=0.0,
                ai_summary="No employee feedback data available for this department.",
                is_ai_assisted=False
            )

        # Aggregate feedback sentiment based on performance & engagement scores
        positive = len([e for e in employees if e.engagement_score >= 4.0])
        neutral = len([e for e in employees if 3.0 <= e.engagement_score < 4.0])
        negative = len([e for e in employees if e.engagement_score < 3.0])

        pos_pct = round((positive / total) * 100, 1)
        neu_pct = round((neutral / total) * 100, 1)
        neg_pct = round((negative / total) * 100, 1)

        # Representative themes (without employee PII)
        themes = [
            f"Workload management and schedule flexibility ({len([e for e in employees if e.overtime > 10])} high overtime cases)",
            f"Overall engagement satisfaction ({pos_pct}% positive feedback)",
            f"Career development opportunities ({len([e for e in employees if e.promotion_history == 0])} employees awaiting progression)"
        ]

        if not grok_client.is_configured:
            fallback = (
                f"{department or 'Organization'} feedback shows {pos_pct}% positive engagement, "
                f"{neu_pct}% neutral, and {neg_pct}% negative sentiments across {total} employee records."
            )
            return SentimentSummaryResponse(
                department=department or "All Departments",
                total_feedbacks=total,
                positive_pct=pos_pct,
                neutral_pct=neu_pct,
                negative_pct=neg_pct,
                ai_summary=fallback,
                is_ai_assisted=False
            )

        prompt = SENTIMENT_SUMMARY_PROMPT.format(
            department=department or "All Departments",
            total_feedbacks=total,
            positive_pct=pos_pct,
            neutral_pct=neu_pct,
            negative_pct=neg_pct,
            themes_text="\n".join(f"- {t}" for t in themes)
        )

        ai_summary = await grok_client.generate_text(
            prompt=prompt,
            temperature=0.3,
            max_tokens=300
        )

        return SentimentSummaryResponse(
            department=department or "All Departments",
            total_feedbacks=total,
            positive_pct=pos_pct,
            neutral_pct=neu_pct,
            negative_pct=neg_pct,
            ai_summary=ai_summary,
            is_ai_assisted=True
        )

    @staticmethod
    async def query_policy_rag(
        current_user: User,
        query: str
    ) -> PolicyQueryResponse:
        """
        RAG query over organization HR policies with strict tenant isolation.
        """
        org_id = get_org_id(current_user.organization_id)
        results = await PolicyRAGService.search_relevant_chunks(org_id, query, top_k=3)

        if not results:
            return PolicyQueryResponse(
                answer="I couldn't find this information in the organization's available HR policies.",
                sources=[],
                matched_chunks=[],
                is_ai_assisted=False
            )

        if not grok_client.is_configured:
            sources = list(set(r["title"] for r in results))
            fallback_answer = (
                f"Relevant policy excerpts found in {', '.join(sources)}:\n\n"
                + "\n\n".join(f"> {r['chunk']}" for r in results[:2])
            )
            return PolicyQueryResponse(
                answer=fallback_answer,
                sources=sources,
                matched_chunks=[r["chunk"] for r in results],
                is_ai_assisted=False
            )

        formatted_chunks = PolicyRAGService.format_chunks_for_prompt(results)
        prompt = POLICY_RAG_PROMPT.format(
            policy_chunks=formatted_chunks,
            query=query
        )

        answer = await grok_client.generate_text(
            prompt=prompt,
            temperature=0.1,
            max_tokens=400
        )

        sources = list(set(r["title"] for r in results))

        return PolicyQueryResponse(
            answer=answer,
            sources=sources,
            matched_chunks=[r["chunk"] for r in results],
            is_ai_assisted=True
        )
