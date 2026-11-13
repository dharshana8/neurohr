import re
import os
from typing import Dict, Any, List, Optional
import pypdf
import docx

KNOWN_SKILLS = [
    "Python", "FastAPI", "React", "Node.js", "JavaScript", "TypeScript", "SQL", "PostgreSQL", 
    "MongoDB", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "Java", "C++", "C#", 
    "HTML", "CSS", "Tailwind", "TailwindCSS", "REST API", "GraphQL", "PyTorch", "TensorFlow", 
    "Scikit-Learn", "Pandas", "NumPy", "XGBoost", "Data Analysis", "Machine Learning", 
    "Deep Learning", "NLP", "Agile", "Scrum", "CI/CD", "Linux", "DevOps", "Microservices", 
    "Redis", "Kafka", "Flutter", "Android", "iOS", "Swift", "Kotlin", "Go", "Golang", 
    "PHP", "Laravel", "Django", "Flask", "Express", "Next.js", "Vue", "Angular"
]

DEGREE_PATTERNS = [
    (r"\bB\.?E\.?\b|\bB\.?Tech\b|\bBachelor of Engineering\b|\bBachelor of Technology\b", "B.E / B.Tech"),
    (r"\bM\.?Tech\b|\bM\.?E\.?\b|\bMaster of Technology\b|\bMaster of Engineering\b", "M.E / M.Tech"),
    (r"\bM\.?C\.?A\.?\b|\bMaster of Computer Applications\b", "MCA"),
    (r"\bB\.?C\.?A\.?\b|\bBachelor of Computer Applications\b", "BCA"),
    (r"\bB\.?Sc\b|\bBachelor of Science\b", "B.Sc"),
    (r"\bM\.?Sc\b|\bMaster of Science\b", "M.Sc"),
    (r"\bPh\.?D\b|\bDoctorate\b", "Ph.D"),
    (r"\bMBA\b|\bMaster of Business Administration\b", "MBA")
]

COMPANY_INDICATORS = ["Inc", "Ltd", "LLC", "Corp", "Technologies", "Services", "Solutions", "Pvt Ltd", "Private Limited", "Group", "Labs"]
JOB_TITLE_KEYWORDS = ["Developer", "Engineer", "Architect", "Manager", "Analyst", "Lead", "Consultant", "Designer", "Administrator", "Intern"]

def extract_text_from_pdf(file_path: str) -> str:
    try:
        reader = pypdf.PdfReader(file_path)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    try:
        doc = docx.Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs if p.text])
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join([cell.text.strip() for cell in row.cells if cell.text.strip()])
                if row_text:
                    text += "\n" + row_text
        return text
    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
        return ""

def extract_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    return ""

def parse_resume_text(text: str) -> Dict[str, Any]:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    # 1. Email extraction
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    email = email_match.group(0) if email_match else None

    # 2. Phone extraction
    phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+?\d{10,12}', text)
    phone = phone_match.group(0) if phone_match else None

    # 3. Name extraction
    name = None
    for line in lines[:5]:
        # Skip header metadata lines
        if any(w in line.lower() for w in ["resume", "curriculum", "cv", "email", "phone", "profile", "contact"]):
            continue
        # If line contains 2-4 words, starts capitalized, no numbers/symbols
        words = line.split()
        if 2 <= len(words) <= 4 and all(re.match(r'^[A-Z][a-zA-Z\.\'-]*$', w) for w in words):
            name = line
            break
    if not name and lines:
        # Fallback to first line if reasonably short
        first_line = lines[0]
        if len(first_line.split()) <= 4 and not any(char.isdigit() for char in first_line):
            name = first_line

    # 4. Degree & Education extraction
    degree = None
    for pattern, deg_name in DEGREE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            degree = deg_name
            break
            
    education = None
    edu_keywords = ["University", "College", "Institute", "School", "Bachelor", "Master", "Degree", "B.E", "B.Tech", "MCA"]
    edu_lines = []
    for line in lines:
        if any(kw in line for kw in edu_keywords):
            edu_lines.append(line)
    if edu_lines:
        education = " | ".join(edu_lines[:2])
    elif degree:
        education = degree

    # 5. Experience extraction (years)
    experience_years = 0.0
    exp_matches = re.findall(r'(\d+(?:\.\d+)?)\+?\s*(?:years|yrs|year)\s*(?:of)?\s*(?:experience|exp)?', text, re.IGNORECASE)
    if exp_matches:
        try:
            experience_years = max([float(m) for m in exp_matches])
        except ValueError:
            experience_years = 0.0
    else:
        # Check for year ranges e.g. 2019 - 2023 or 2021 - Present
        year_ranges = re.findall(r'\b(20\d{2})\s*[-–]\s*(20\d{2}|present|current)\b', text, re.IGNORECASE)
        total_yrs = 0.0
        for start_yr, end_yr in year_ranges:
            try:
                sy = int(start_yr)
                ey = 2026 if end_yr.lower() in ["present", "current"] else int(end_yr)
                if ey > sy:
                    total_yrs += (ey - sy)
            except ValueError:
                pass
        if total_yrs > 0:
            experience_years = round(total_yrs, 1)

    # 6. Skills extraction
    extracted_skills = []
    text_lower = text.lower()
    for skill in KNOWN_SKILLS:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            extracted_skills.append(skill)
            
    # Remove duplicate skill variations if any
    extracted_skills = list(dict.fromkeys(extracted_skills))

    # 7. Projects extraction
    projects = []
    in_projects_sec = False
    for line in lines:
        if any(h in line.lower() for h in ["projects", "personal projects", "key projects"]):
            in_projects_sec = True
            continue
        elif in_projects_sec and any(h in line.lower() for h in ["experience", "education", "skills", "certifications"]):
            in_projects_sec = False
        if in_projects_sec and len(line) > 5:
            projects.append(line)
            if len(projects) >= 4:
                break

    # 8. Certifications extraction
    certifications = []
    in_cert_sec = False
    for line in lines:
        if any(h in line.lower() for h in ["certifications", "certificates", "licenses"]):
            in_cert_sec = True
            continue
        elif in_cert_sec and any(h in line.lower() for h in ["experience", "education", "skills", "projects"]):
            in_cert_sec = False
        if in_cert_sec and len(line) > 3:
            certifications.append(line)
            if len(certifications) >= 3:
                break

    # 9. Previous Companies & Job Titles extraction
    previous_companies = []
    job_titles = []
    for line in lines:
        for ind in COMPANY_INDICATORS:
            if ind.lower() in line.lower() and len(line) < 60:
                previous_companies.append(line)
                break
        for title_kw in JOB_TITLE_KEYWORDS:
            if title_kw.lower() in line.lower() and len(line) < 50:
                job_titles.append(line)
                break

    previous_companies = list(dict.fromkeys(previous_companies))[:3]
    job_titles = list(dict.fromkeys(job_titles))[:3]

    # Status check
    missing_fields = []
    if not name: missing_fields.append("name")
    if not email: missing_fields.append("email")
    if not extracted_skills: missing_fields.append("skills")
    if not degree and not education: missing_fields.append("education")

    parsing_status = "Completed"
    parsing_warning = None
    if missing_fields or len(text.strip()) < 50:
        parsing_status = "Partial"
        parsing_warning = f"Some information could not be extracted automatically ({', '.join(missing_fields) if missing_fields else 'sparse text'})."

    return {
        "name": name if name else "Candidate",
        "email": email,
        "phone": phone,
        "education": education,
        "degree": degree,
        "experience": experience_years,
        "skills": extracted_skills,
        "projects": projects,
        "certifications": certifications,
        "previous_companies": previous_companies,
        "job_titles": job_titles,
        "resume_text": text,
        "parsing_status": parsing_status,
        "parsing_warning": parsing_warning
    }
