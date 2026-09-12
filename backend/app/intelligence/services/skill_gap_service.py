from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timezone
import re

from app.models.employee import Employee
from app.models.intelligence import Skill, RoleSkillRequirement, SkillGapAnalysis
from app.models.audit import AuditLog

DEFAULT_TAXONOMY = [
    {"name": "Python", "category": "Backend", "aliases": ["python3", "python programming", "py"]},
    {"name": "FastAPI", "category": "Backend", "aliases": ["fastapi", "fast-api"]},
    {"name": "React", "category": "Frontend", "aliases": ["reactjs", "react.js", "react-native"]},
    {"name": "TypeScript", "category": "Frontend", "aliases": ["ts", "typescript"]},
    {"name": "Docker", "category": "DevOps", "aliases": ["docker engine", "containerization", "containers"]},
    {"name": "AWS", "category": "Cloud", "aliases": ["amazon web services", "aws cloud", "cloud aws"]},
    {"name": "MongoDB", "category": "Database", "aliases": ["mongo", "mongodb", "nosql"]},
    {"name": "SQL", "category": "Database", "aliases": ["postgresql", "mysql", "postgres", "relational database"]},
    {"name": "Kubernetes", "category": "DevOps", "aliases": ["k8s", "kubernetes cluster"]},
    {"name": "Node.js", "category": "Backend", "aliases": ["node", "nodejs"]},
    {"name": "Machine Learning", "category": "AI/ML", "aliases": ["ml", "ai/ml", "artificial intelligence", "scikit-learn"]},
    {"name": "Git", "category": "Tools", "aliases": ["github", "gitlab", "version control"]},
    {"name": "CI/CD", "category": "DevOps", "aliases": ["continuous integration", "github actions", "jenkins"]},
    {"name": "Communication", "category": "Soft Skills", "aliases": ["team communication", "presentation"]},
    {"name": "Leadership", "category": "Soft Skills", "aliases": ["team lead", "mentorship", "management"]},
]

PROFICIENCY_WEIGHTS = {
    "BEGINNER": 1,
    "INTERMEDIATE": 2,
    "ADVANCED": 3,
    "EXPERT": 4,
    "UNKNOWN": 0
}

def get_org_id(org_link):
    if hasattr(org_link, "ref"):
        return org_link.ref.id
    if hasattr(org_link, "id"):
        return org_link.id
    return org_link

class SkillGapService:
    @staticmethod
    async def ensure_default_taxonomy():
        """Ensure standard platform skills are seeded if DB is empty."""
        count = await Skill.find({"organization_id": None}).count()
        if count == 0:
            skills_to_insert = [
                Skill(
                    name=item["name"],
                    category=item["category"],
                    aliases=item["aliases"],
                    description=f"Standard skill for {item['name']}",
                    organization_id=None
                )
                for item in DEFAULT_TAXONOMY
            ]
            await Skill.insert_many(skills_to_insert)

    @staticmethod
    async def get_skill_alias_map(org_id) -> Dict[str, str]:
        """
        Build alias to canonical skill name mapping.
        Includes global platform taxonomy (org_id is None) and tenant-specific skills.
        """
        await SkillGapService.ensure_default_taxonomy()
        
        # Fetch both global skills and tenant-specific skills
        skills = await Skill.find({
            "$or": [
                {"organization_id": None},
                {"organization_id.$id": org_id}
            ]
        }).to_list()

        alias_map = {}
        for s in skills:
            canonical = s.name.strip()
            alias_map[canonical.lower()] = canonical
            for alias in s.aliases:
                alias_clean = alias.strip().lower()
                if alias_clean:
                    alias_map[alias_clean] = canonical
        return alias_map

    @staticmethod
    def parse_and_normalize_employee_skills(raw_skills: str, alias_map: Dict[str, str]) -> Dict[str, str]:
        """
        Extract skills from employee's skills string and normalize to canonical taxonomy names.
        Returns dict of {canonical_skill: proficiency_level}.
        Defaults proficiency to UNKNOWN unless specified.
        """
        if not raw_skills:
            return {}
            
        employee_skills = {}
        # Support comma, semicolon, newline or slash separation
        tokens = re.split(r'[,;\n/]+', raw_skills)
        for token in tokens:
            cleaned = token.strip()
            if not cleaned:
                continue
            
            # Check if proficiency is encoded in token, e.g., "Python (Advanced)" or "React: Intermediate"
            level = "UNKNOWN"
            for prof in ["BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT"]:
                if re.search(rf'\b{prof}\b', cleaned, re.IGNORECASE):
                    level = prof
                    cleaned = re.sub(rf'[\(:\-\]]*\s*{prof}\s*[\)]*', '', cleaned, flags=re.IGNORECASE).strip()
                    break

            cleaned_lower = cleaned.lower()
            canonical = alias_map.get(cleaned_lower, cleaned)
            employee_skills[canonical] = level

        return employee_skills

    @staticmethod
    async def analyze_gap(
        employee_id: str,
        target_role: str,
        org_id,
        user=None
    ) -> SkillGapAnalysis:
        """
        Deterministic skill gap analysis between employee current skills and target role requirements.
        Strictly isolated to authenticated organization.
        """
        # 1. Retrieve employee
        employee = await Employee.find_one(
            {"organization_id.$id": org_id},
            Employee.employee_id == employee_id
        )
        if not employee:
            raise ValueError(f"Employee {employee_id} not found in this organization")

        # 2. Build taxonomy alias map
        alias_map = await SkillGapService.get_skill_alias_map(org_id)

        # 3. Normalize employee skills
        emp_skills_dict = SkillGapService.parse_and_normalize_employee_skills(employee.skills, alias_map)

        # 4. Retrieve target role requirements for organization
        # Case-insensitive role matching
        role_req = await RoleSkillRequirement.find_one(
            {"organization_id.$id": org_id},
            {"role": {"$regex": f"^{re.escape(target_role.strip())}$", "$options": "i"}}
        )

        # If no custom org role requirement exists, fallback or build from known defaults
        required_skills = []
        preferred_skills = []
        skill_levels = {}

        if role_req:
            required_skills = role_req.required_skills
            preferred_skills = role_req.preferred_skills
            skill_levels = role_req.skill_levels
        else:
            # Create a sensible initial default if target role matches common roles
            role_clean = target_role.strip().lower()
            if "backend" in role_clean:
                required_skills = ["Python", "FastAPI", "MongoDB"]
                preferred_skills = ["Docker", "AWS"]
                skill_levels = {"Python": "ADVANCED", "FastAPI": "INTERMEDIATE", "MongoDB": "INTERMEDIATE", "Docker": "BEGINNER", "AWS": "BEGINNER"}
            elif "frontend" in role_clean:
                required_skills = ["React", "TypeScript"]
                preferred_skills = ["Docker", "CI/CD"]
                skill_levels = {"React": "ADVANCED", "TypeScript": "INTERMEDIATE"}
            elif "data" in role_clean:
                required_skills = ["Python", "SQL", "Machine Learning"]
                preferred_skills = ["Docker", "AWS"]
                skill_levels = {"Python": "ADVANCED", "SQL": "ADVANCED"}
            else:
                # Default generic requirement based on current employee role + target
                required_skills = [s for s in list(emp_skills_dict.keys())[:3]] or ["Communication", "Leadership"]
                preferred_skills = ["Leadership"]

        # Normalize role required & preferred skills against taxonomy
        normalized_required = [alias_map.get(s.lower(), s) for s in required_skills]
        normalized_preferred = [alias_map.get(s.lower(), s) for s in preferred_skills]

        matched_skills = []
        missing_skills = []
        partial_skills = []
        recommendations = []

        total_req_count = len(normalized_required)

        # Evaluate Required Skills
        for req_skill in normalized_required:
            req_level = skill_levels.get(req_skill, "UNKNOWN")
            
            # Check if employee has this skill
            if req_skill in emp_skills_dict:
                emp_level = emp_skills_dict[req_skill]
                
                # Proficiency check
                req_weight = PROFICIENCY_WEIGHTS.get(req_level, 0)
                emp_weight = PROFICIENCY_WEIGHTS.get(emp_level, 0)
                
                if req_weight > 0 and emp_weight > 0 and emp_weight < req_weight:
                    # Partial skill gap: Has skill, but below required proficiency level
                    partial_skills.append({
                        "skill": req_skill,
                        "required_level": req_level,
                        "employee_level": emp_level,
                        "status": "PARTIAL",
                        "explanation": f"Employee has {req_skill} ({emp_level}), but {target_role} expects {req_level} proficiency."
                    })
                    recommendations.append({
                        "skill": req_skill,
                        "priority": "HIGH",
                        "recommendation_type": "PROJECT",
                        "recommendation": f"Advanced {req_skill} practical project",
                        "reason": f"Target role expects {req_level} proficiency in {req_skill}. Employee currently demonstrates {emp_level} level."
                    })
                else:
                    # Matched!
                    matched_skills.append({
                        "skill": req_skill,
                        "required_level": req_level,
                        "employee_level": emp_level,
                        "status": "MATCHED",
                        "explanation": f"Required skill {req_skill} is present in employee profile."
                    })
            else:
                # Missing required skill
                missing_skills.append({
                    "skill": req_skill,
                    "required_level": req_level,
                    "employee_level": "NONE",
                    "status": "MISSING",
                    "explanation": f"Required skill {req_skill} is not present in employee profile."
                })
                recommendations.append({
                    "skill": req_skill,
                    "priority": "HIGH",
                    "recommendation_type": "TRAINING",
                    "recommendation": f"{req_skill} fundamentals training",
                    "reason": f"{req_skill} is required for target role '{target_role}' but is not present in employee profile."
                })

        # Evaluate Preferred Skills
        for pref_skill in normalized_preferred:
            pref_level = skill_levels.get(pref_skill, "UNKNOWN")
            if pref_skill in emp_skills_dict:
                matched_skills.append({
                    "skill": pref_skill,
                    "required_level": pref_level,
                    "employee_level": emp_skills_dict[pref_skill],
                    "status": "MATCHED_PREFERRED",
                    "explanation": f"Preferred skill {pref_skill} is present in employee profile."
                })
            else:
                missing_skills.append({
                    "skill": pref_skill,
                    "required_level": pref_level,
                    "employee_level": "NONE",
                    "status": "MISSING_PREFERRED",
                    "explanation": f"Preferred skill {pref_skill} is not currently recorded for employee."
                })
                recommendations.append({
                    "skill": pref_skill,
                    "priority": "MEDIUM",
                    "recommendation_type": "MENTORING",
                    "recommendation": f"{pref_skill} introductory mentoring & learning",
                    "reason": f"{pref_skill} is a preferred/recommended skill for '{target_role}' and will strengthen candidate readiness."
                })

        # Deterministic Skill Coverage Formula:
        # Full match = 1.0, Partial match = 0.5
        # Skill Coverage % = (matched_required + 0.5 * partial_required) / total_required * 100
        if total_req_count == 0:
            coverage_score = 100.0
        else:
            full_matches = len([m for m in matched_skills if m.get("status") == "MATCHED"])
            partial_matches = len(partial_skills)
            coverage_score = round(((full_matches + (0.5 * partial_matches)) / total_req_count) * 100.0, 2)
            coverage_score = min(coverage_score, 100.0)

        # Save analysis record
        org_ref = employee.organization_id.to_ref() if hasattr(employee.organization_id, "to_ref") else employee.organization_id
        analysis = SkillGapAnalysis(
            organization_id=org_ref,
            employee_id=employee.employee_id,
            current_role=employee.role,
            target_role=target_role,
            skill_coverage_score=coverage_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            partial_skills=partial_skills,
            recommended_development_areas=recommendations,
            created_at=datetime.now(timezone.utc)
        )
        await analysis.insert()

        # Audit Log
        if user:
            user_ref = user.to_ref() if hasattr(user, "to_ref") else user
            audit = AuditLog(
                user_id=user_ref,
                organization_id=org_ref,
                action="SKILL_GAP_ANALYZED",
                resource_type="SkillGapAnalysis",
                resource_id=analysis.analysis_id,
                status="SUCCESS"
            )
            await audit.insert()

        return analysis
