import pandas as pd
from io import StringIO
from typing import List, Dict, Any
import math
import re
from fastapi import UploadFile
from app.integrations.base.connector import BaseConnector
from app.integrations.base.schemas import NormalizedEmployee
from app.models.employee import Employee
from app.models.user import User
from app.schemas.workforce import ImportSummaryResponse
from datetime import datetime, timezone

class CSVConnector(BaseConnector):
    """Connector for CSV file uploads.
    It validates, normalizes, and upserts employee records.
    """

    def __init__(self, file: UploadFile, user: User):
        self.file = file
        self.user = user
        self.org_id = self._get_org_id(user.organization_id)

    @staticmethod
    def _get_org_id(org_link) -> Any:
        if hasattr(org_link, "ref"):
            return org_link.ref.id
        if hasattr(org_link, "id"):
            return org_link.id
        return org_link

    async def authenticate(self, credentials: Dict[str, Any] | None = None) -> bool:
        # CSV does not require authentication beyond the API token.
        return True

    async def test_connection(self) -> bool:
        # Always true for a local file upload.
        return True

    async def fetch_employees(self) -> List[Dict[str, Any]]:
        # Read CSV content from the uploaded file.
        contents = await self.file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
        return df.to_dict(orient="records")

    async def fetch_departments(self) -> List[Dict[str, Any]]:
        return []

    async def fetch_roles(self) -> List[Dict[str, Any]]:
        return []

    async def fetch_performance(self) -> List[Dict[str, Any]]:
        return []

    async def fetch_skills(self) -> List[Dict[str, Any]]:
        return []

    async def sync(self) -> ImportSummaryResponse:
        # Load raw rows
        raw_rows = await self.fetch_employees()
        required_columns = [
            "employee_id",
            "name",
            "department",
            "role",
            "joining_date",
            "experience",
            "salary",
            "performance_score",
            "engagement_score",
            "overtime",
            "skills",
            "promotion_history",
            "manager_feedback",
            "employment_status",
            "attrition",
        ]
        # Validate columns
        missing = [c for c in required_columns if c not in raw_rows[0].keys()]
        if missing:
            raise ValueError(f"Missing required CSV columns: {missing}")

        # Fetch existing employee IDs for organization isolation
        existing = await Employee.find({"organization_id.$id": self.org_id}).to_list()
        existing_ids = {e.employee_id for e in existing}
        seen_batch_ids = set()
        new_employees: List[Employee] = []
        errors: List[str] = []
        total_rows = len(raw_rows)
        valid_rows = 0
        invalid_rows = 0

        for idx, row in enumerate(raw_rows, start=2):  # start at 2 to match CSV line numbers
            row_errors: List[str] = []
            # Basic duplicate checks
            emp_id = str(row.get("employee_id", "")).strip()
            if not emp_id:
                row_errors.append(f"Row {idx}: Missing employee_id")
            elif emp_id in seen_batch_ids or emp_id in existing_ids:
                row_errors.append(f"Row {idx}: Duplicate employee_id")
            else:
                seen_batch_ids.add(emp_id)

            # Minimal required field checks (name, department, role)
            for field in ["name", "department", "role"]:
                if not str(row.get(field, "")).strip():
                    row_errors.append(f"Row {idx}: Missing required field {field}")

            # Date parsing
            try:
                joining_date = pd.to_datetime(row.get("joining_date")).to_pydatetime()
            except Exception:
                row_errors.append(f"Row {idx}: Invalid joining_date")
                joining_date = datetime.now(timezone.utc)

            # Numeric conversions with robust fallbacks
            def safe_float(val, name):
                if val is None or pd.isnull(val):
                    return 0.0
                if isinstance(val, (int, float)):
                    return float(val) if not math.isnan(val) else 0.0
                val_str = str(val).replace("$", "").replace(",", "").strip()
                if not val_str:
                    return 0.0
                try:
                    res = float(val_str)
                    if math.isnan(res):
                        row_errors.append(f"Row {idx}: Invalid {name}")
                        return 0.0
                    return res
                except Exception:
                    row_errors.append(f"Row {idx}: Invalid {name}")
                    return 0.0

            def safe_int(val, name):
                if val is None or pd.isnull(val):
                    return 0
                if isinstance(val, (int, float)):
                    return int(val) if not math.isnan(val) else 0
                val_str = str(val).replace(",", "").strip()
                if not val_str:
                    return 0
                try:
                    return int(float(val_str))
                except Exception:
                    row_errors.append(f"Row {idx}: Invalid {name}")
                    return 0

            def safe_overtime(val):
                if val is None or pd.isnull(val):
                    return 0.0
                if isinstance(val, (int, float)):
                    return float(val) if not math.isnan(val) else 0.0
                val_str = str(val).strip()
                if not val_str:
                    return 0.0
                lower = val_str.lower()
                if lower in ("yes", "y", "true", "t", "overtime"):
                    return 1.0
                if lower in ("no", "n", "false", "f", "none", "na", "n/a", "0", "0.0"):
                    return 0.0
                try:
                    res = float(val_str)
                    if not math.isnan(res):
                        return res
                except ValueError:
                    pass
                cleaned = re.sub(r"[^\d.]", "", val_str)
                if cleaned:
                    try:
                        res = float(cleaned)
                        if not math.isnan(res):
                            return res
                    except ValueError:
                        pass
                row_errors.append(f"Row {idx}: Invalid overtime")
                return 0.0

            def safe_attrition(val):
                if val is None or pd.isnull(val):
                    return 0
                if isinstance(val, (int, float)):
                    int_val = int(val)
                    if int_val in (0, 1):
                        return int_val
                val_str = str(val).strip().lower()
                if val_str in ("1", "yes", "y", "true", "t"):
                    return 1
                if val_str in ("0", "no", "n", "false", "f"):
                    return 0
                try:
                    int_val = int(float(val_str))
                    if int_val in (0, 1):
                        return int_val
                except Exception:
                    pass
                row_errors.append(f"Row {idx}: attrition must be 0 or 1")
                return 0

            experience = safe_float(row.get("experience"), "experience")
            salary = safe_float(row.get("salary"), "salary")
            performance_score = safe_float(row.get("performance_score"), "performance_score")
            engagement_score = safe_float(row.get("engagement_score"), "engagement_score")
            overtime = safe_overtime(row.get("overtime"))
            promotion_history = safe_int(row.get("promotion_history"), "promotion_history")
            attrition = safe_attrition(row.get("attrition"))

            # Skills list handling (supports commas and semicolons)
            skills_raw = row.get("skills", "")
            skills = [s.strip() for s in re.split(r"[,;]", str(skills_raw)) if s.strip() and s.lower() != "nan"]

            if row_errors:
                errors.extend(row_errors)
                invalid_rows += 1
                continue

            # Build Employee document
            org_ref = self.user.organization_id.to_ref() if hasattr(self.user.organization_id, "to_ref") else self.user.organization_id
            employee = Employee(
                organization_id=org_ref,
                employee_id=emp_id,
                name=str(row.get("name")).strip(),
                department=str(row.get("department")).strip(),
                role=str(row.get("role")).strip(),
                joining_date=joining_date,
                experience=experience,
                salary=salary,
                performance_score=performance_score,
                engagement_score=engagement_score,
                overtime=overtime,
                skills=", ".join(skills),
                promotion_history=promotion_history,
                manager_feedback=str(row.get("manager_feedback", "")),
                employment_status=str(row.get("employment_status", "Active")),
                attrition=attrition,
            )
            new_employees.append(employee)
            valid_rows += 1

        if new_employees:
            await Employee.insert_many(new_employees)

        return ImportSummaryResponse(
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            imported_rows=len(new_employees),
            errors=errors,
        )

    async def disconnect(self) -> None:
        # No persistent connection for CSV files.
        return None
