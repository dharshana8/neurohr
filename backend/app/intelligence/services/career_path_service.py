from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import uuid

from app.models.employee import Employee
from app.models.intelligence import CareerPath, SkillGapAnalysis
from app.models.audit import AuditLog
from app.intelligence.services.skill_gap_service import SkillGapService, get_org_id

class CareerPathService:
    @staticmethod
    async def generate_career_path(
        employee_id: str,
        target_role: str,
        org_id,
        user=None
    ) -> CareerPath:
        """
        Generate an AI-assisted personalized career path for an employee toward a target role.
        Calculates gap, formulates structured milestones, and stores supporting context.
        """
        # 1. Retrieve employee
        employee = await Employee.find_one(
            {"organization_id.$id": org_id},
            Employee.employee_id == employee_id
        )
        if not employee:
            raise ValueError(f"Employee {employee_id} not found in this organization")

        # 2. Run / retrieve skill gap analysis
        analysis = await SkillGapService.analyze_gap(
            employee_id=employee_id,
            target_role=target_role,
            org_id=org_id,
            user=user
        )

        missing_skill_names = [m["skill"] for m in analysis.missing_skills if m.get("status") == "MISSING"]
        pref_missing = [m["skill"] for m in analysis.missing_skills if m.get("status") == "MISSING_PREFERRED"]
        partial_skill_names = [p["skill"] for p in analysis.partial_skills]
        matched_skill_names = [m["skill"] for m in analysis.matched_skills]

        all_gap_skills = missing_skill_names + partial_skill_names

        # 3. Generate Recommended Actions based on actual data
        recommended_actions = []
        for s in missing_skill_names[:3]:
            recommended_actions.append(f"Complete foundational competency and practical training in {s}")
        for s in partial_skill_names[:2]:
            recommended_actions.append(f"Deepen proficiency in {s} through advanced project work")
        for s in pref_missing[:2]:
            recommended_actions.append(f"Explore preferred capability: {s}")

        if not recommended_actions:
            recommended_actions.append(f"Demonstrate leadership and cross-functional mentoring in {employee.role}")
            recommended_actions.append(f"Take ownership of high-impact strategic initiatives")

        recommended_actions.append("Present technical portfolio / deliverables for HR and management readiness review")

        # 4. Formulate Progressive Milestones
        milestones = []
        # Milestone 1: Foundation
        if missing_skill_names:
            skills_text = ", ".join(missing_skill_names[:2])
            milestones.append({
                "title": f"Phase 1: Core Skill Acquisition ({skills_text})",
                "description": f"Undergo targeted training and build fundamental understanding of {skills_text}.",
                "completed": False,
                "target_date": None
            })
        else:
            milestones.append({
                "title": "Phase 1: Baseline Competency Assessment",
                "description": f"Validate existing technical competencies against target role requirements.",
                "completed": True,
                "target_date": None
            })

        # Milestone 2: Practical Application
        app_skills = partial_skill_names or missing_skill_names or ["system architecture"]
        milestones.append({
            "title": f"Phase 2: Applied Project & Delivery",
            "description": f"Deliver a practical end-to-end assignment integrating {', '.join(app_skills[:2])}.",
            "completed": False,
            "target_date": None
        })

        # Milestone 3: Expansion & Mentorship
        milestones.append({
            "title": "Phase 3: Cross-Functional Demonstration & Peer Collaboration",
            "description": f"Share knowledge, conduct peer code reviews, and demonstrate operational proficiency in {target_role} expectations.",
            "completed": False,
            "target_date": None
        })

        # Milestone 4: Review Checkpoint
        milestones.append({
            "title": "Phase 4: Manager & HR Career Review",
            "description": "Comprehensive review of progress milestones, work deliverables, and role readiness evaluation.",
            "completed": False,
            "target_date": None
        })

        # Supporting Performance & Experience Context
        perf_context = {
            "performance_score": employee.performance_score,
            "engagement_score": employee.engagement_score,
            "experience_years": employee.experience,
            "notes": "Performance score is presented as non-guaranteed supporting context. Recommendations are advisory decision support."
        }

        # Check if an active career path already exists for this employee and target role
        existing = await CareerPath.find_one(
            {"organization_id.$id": org_id},
            CareerPath.employee_id == employee_id,
            CareerPath.target_role == target_role,
            CareerPath.status == "ACTIVE"
        )

        org_ref = employee.organization_id.to_ref() if hasattr(employee.organization_id, "to_ref") else employee.organization_id

        if existing:
            # Update existing
            existing.estimated_skill_coverage = analysis.skill_coverage_score
            existing.required_skills = [m["skill"] for m in analysis.matched_skills] + missing_skill_names
            existing.current_skills = matched_skill_names
            existing.missing_skills = all_gap_skills
            existing.recommended_actions = recommended_actions
            existing.milestones = milestones
            existing.performance_context = perf_context
            existing.updated_at = datetime.now(timezone.utc)
            await existing.save()
            career_path = existing
            action_event = "CAREER_PATH_GENERATED"
        else:
            career_path = CareerPath(
                organization_id=org_ref,
                employee_id=employee_id,
                current_role=employee.role,
                target_role=target_role,
                estimated_skill_coverage=analysis.skill_coverage_score,
                required_skills=[m["skill"] for m in analysis.matched_skills] + missing_skill_names,
                current_skills=matched_skill_names,
                missing_skills=all_gap_skills,
                recommended_actions=recommended_actions,
                milestones=milestones,
                status="ACTIVE",
                performance_context=perf_context,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            await career_path.insert()
            action_event = "CAREER_PATH_GENERATED"

        # Audit Log
        if user:
            user_ref = user.to_ref() if hasattr(user, "to_ref") else user
            audit = AuditLog(
                user_id=user_ref,
                organization_id=org_ref,
                action=action_event,
                resource_type="CareerPath",
                resource_id=career_path.career_path_id,
                status="SUCCESS"
            )
            await audit.insert()

        return career_path
