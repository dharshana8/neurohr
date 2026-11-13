import re
from typing import Dict, Any, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.models.job import Job
from app.models.candidate import Candidate

def compute_candidate_job_match(job: Job, candidate: Candidate) -> Dict[str, Any]:
    # 1. Skill Matching
    req_skills = [s.strip() for s in job.required_skills if s.strip()]
    cand_skills_raw = set([s.strip().lower() for s in candidate.skills if s.strip()])
    
    # Also check if required skills appear in raw resume text
    resume_text_lower = (candidate.resume_text or "").lower()
    
    matched_skills = []
    missing_skills = []
    
    for req_s in req_skills:
        req_lower = req_s.lower()
        # Check skill in candidate.skills array or exact match in resume text
        if req_lower in cand_skills_raw or re.search(r'\b' + re.escape(req_lower) + r'\b', resume_text_lower):
            matched_skills.append(req_s)
        else:
            missing_skills.append(req_s)

    if req_skills:
        skill_score = (len(matched_skills) / len(req_skills)) * 100.0
    else:
        skill_score = 100.0

    # 2. Experience Matching
    min_exp = float(job.minimum_experience or 0.0)
    cand_exp = float(candidate.experience or 0.0)
    
    if min_exp == 0.0:
        exp_match_status = "Match"
        exp_score = 100.0
    elif cand_exp >= min_exp:
        exp_match_status = "Exceeds" if cand_exp >= (min_exp + 2.0) else "Match"
        exp_score = 100.0
    elif cand_exp > 0:
        exp_match_status = "Below Minimum"
        exp_score = min(90.0, (cand_exp / min_exp) * 100.0)
    else:
        exp_match_status = "Below Minimum"
        exp_score = 25.0

    # 3. Education / Qualification Matching
    job_qual = (job.qualification or "").strip().lower()
    cand_deg = (candidate.degree or "").strip()
    cand_edu = (candidate.education or "").strip()

    if not job_qual:
        edu_match_status = "Match"
        edu_score = 100.0
    elif cand_deg and any(q.strip().lower() in cand_deg.lower() for q in job_qual.split("/")):
        edu_match_status = "Match"
        edu_score = 100.0
    elif cand_edu and any(q.strip().lower() in cand_edu.lower() for q in job_qual.split("/")):
        edu_match_status = "Match"
        edu_score = 95.0
    elif cand_deg or cand_edu:
        edu_match_status = "Partial Match"
        edu_score = 70.0
    else:
        edu_match_status = "Missing"
        edu_score = 30.0

    # 4. Semantic Similarity (NLP via TF-IDF & Cosine Similarity)
    job_text = f"{job.title} {job.description} {' '.join(req_skills)} {job.qualification}"
    cand_text = f"{candidate.name} {candidate.resume_text} {' '.join(candidate.skills)} {candidate.degree or ''} {candidate.education or ''}"
    
    semantic_sim = 0.0
    if len(job_text.strip()) > 5 and len(cand_text.strip()) > 5:
        try:
            vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform([job_text, cand_text])
            sim_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            semantic_sim = float(sim_matrix[0][0])
        except Exception:
            semantic_sim = 0.5
            
    semantic_sim = min(1.0, max(0.0, semantic_sim))
    semantic_score = semantic_sim * 100.0

    # 5. Weighted Overall Match Score (Skill 40%, Experience 25%, Education 15%, Semantic 20%)
    overall_score = (0.40 * skill_score) + (0.25 * exp_score) + (0.15 * edu_score) + (0.20 * semantic_score)
    overall_score = round(max(0.0, min(100.0, overall_score)), 1)

    # 6. Dynamic Explanation Generation
    reasons = []
    if matched_skills:
        reasons.append(f"Strong skill overlap: {', '.join(matched_skills)}")
    if exp_match_status in ["Match", "Exceeds"]:
        reasons.append(f"Relevant experience ({cand_exp} yrs vs {min_exp} yrs required)")
    if edu_match_status == "Match":
        reasons.append(f"Qualification met ({cand_deg or 'Degree matches'})")
    if semantic_sim >= 0.4:
        reasons.append(f"Strong semantic relevance ({int(semantic_sim * 100)}%)")

    missing_reasons = []
    if missing_skills:
        missing_reasons.append(f"Missing required skills: {', '.join(missing_skills)}")
    if exp_match_status == "Below Minimum":
        missing_reasons.append(f"Experience below minimum requirement ({cand_exp} yrs vs {min_exp} yrs required)")
    if edu_match_status == "Missing":
        missing_reasons.append("Qualification details unverified in resume")

    explanation_str = ""
    if reasons:
        explanation_str += "Positives: " + " | ".join(reasons) + "."
    if missing_reasons:
        if explanation_str:
            explanation_str += " "
        explanation_str += "Gaps: " + " | ".join(missing_reasons) + "."

    return {
        "job_id": job.job_id,
        "candidate_id": candidate.candidate_id,
        "match_score": overall_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "experience_match": exp_match_status,
        "education_match": edu_match_status,
        "semantic_similarity": round(semantic_sim, 2),
        "explanation": explanation_str or "Evaluated based on standard qualifications and skills matching."
    }
