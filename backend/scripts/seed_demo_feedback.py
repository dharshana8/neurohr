import os
import sys
import csv
import asyncio
from datetime import datetime, timezone
import uuid

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticClient
if not hasattr(AgnosticClient, "append_metadata"):
    setattr(AgnosticClient, "append_metadata", lambda self, *args, **kwargs: None)

from beanie import init_beanie
from app.core.config import settings
from app.models.organization import Organization
from app.models.user import User
from app.models.employee import Employee
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.match import CandidateMatch
from app.models.attrition import AttritionPrediction
from app.models.audit import AuditLog
from app.models.intelligence import Skill, RoleSkillRequirement, SkillGapAnalysis, CareerPath
from app.models.ai import AIChatConversation, HRPolicyDocument
from app.models.sentiment import EmployeeFeedback, SentimentResult
from app.intelligence.services.sentiment_service import SentimentAnalysisService, get_org_id


async def seed_demo_feedback():
    print("Connecting to MongoDB at:", settings.MONGODB_URL)
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[
            Organization, User, Employee, Job, Candidate, CandidateMatch,
            AttritionPrediction, AuditLog, Skill, RoleSkillRequirement,
            SkillGapAnalysis, CareerPath, AIChatConversation, HRPolicyDocument,
            EmployeeFeedback, SentimentResult
        ]
    )

    # Find or create demo organization
    org = await Organization.find_one()
    if not org:
        print("Creating default Demo Organization...")
        org = Organization(name="NeuroHR Demo Corp", industry="Technology", company_size="500-1000")
        await org.insert()

    org_id = get_org_id(org)
    org_ref = org.to_ref() if hasattr(org, "to_ref") else org
    print(f"Target Organization: {org.name} (ID: {org_id})")

    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "demo_feedback_data.csv"))
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return

    print(f"Loading synthetic demo records from {csv_path}...")
    feedbacks_to_insert = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fid = row.get("feedback_id", "").strip() or str(uuid.uuid4())
            sub_date = datetime.now(timezone.utc)
            if row.get("submitted_at"):
                try:
                    sub_date = datetime.fromisoformat(row["submitted_at"].replace("Z", "+00:00"))
                except Exception:
                    pass

            # Check if record with this feedback_id already exists in org
            existing = await EmployeeFeedback.find_one({
                "feedback_id": fid,
                "organization_id.$id": org_id
            })
            if existing:
                continue

            fb = EmployeeFeedback(
                feedback_id=fid,
                organization_id=org_ref,
                employee_id=row.get("employee_id", "").strip() or None,
                department=row.get("department", "General").strip(),
                category=row.get("category", "OTHER").strip().upper(),
                feedback_text=row.get("feedback_text", "").strip(),
                source=row.get("source", "SURVEY").strip().upper(),
                submitted_at=sub_date,
                is_synthetic=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            feedbacks_to_insert.append(fb)

    if feedbacks_to_insert:
        await EmployeeFeedback.insert_many(feedbacks_to_insert)
        print(f"Inserted {len(feedbacks_to_insert)} new synthetic feedback records.")
    else:
        print("All records in demo CSV already exist in database.")

    # Run batch sentiment analysis
    all_feedbacks = await EmployeeFeedback.find({"organization_id.$id": org_id}).to_list()
    print(f"Analyzing sentiment for {len(all_feedbacks)} records...")
    total_eval, analyzed, skipped, counts = await SentimentAnalysisService.analyze_batch(all_feedbacks, force_reanalyze=False)

    print(f"Sentiment Analysis Complete:")
    print(f"  Total Evaluated: {total_eval}")
    print(f"  Newly Analyzed: {analyzed}")
    print(f"  Skipped (Cached): {skipped}")
    print(f"  Positive: {counts['POSITIVE']}")
    print(f"  Neutral:  {counts['NEUTRAL']}")
    print(f"  Negative: {counts['NEGATIVE']}")
    print("Demo feedback seeding finished successfully.")


if __name__ == "__main__":
    asyncio.run(seed_demo_feedback())
