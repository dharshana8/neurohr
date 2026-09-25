from typing import Any, List, Dict, Optional
from app.integrations.base.connector import BaseConnector
from app.integrations.utils.synthetic_data import generate_mock_hris_data

class MockHRISConnector(BaseConnector):
    """
    Mock human resource information system connector simulating external systems like
    Workday, BambooHR, SAP SuccessFactors, or Oracle HCM.
    Exposes raw HRIS schemas through structured extraction methods.
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.is_connected = True
        self._cached_employees: Optional[List[Dict[str, Any]]] = None

    async def authenticate(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Simulate secure authentication handshake with external HRIS platform."""
        self.is_connected = True
        return True

    async def test_connection(self) -> bool:
        """Verify API connectivity and endpoint availability against external HRIS."""
        return True

    async def fetch_employees(self) -> List[Dict[str, Any]]:
        """Fetch raw employee profiles from external HRIS API."""
        if not self._cached_employees:
            self._cached_employees = generate_mock_hris_data(count=100)
        return self._cached_employees

    async def fetch_departments(self) -> List[Dict[str, Any]]:
        """Fetch distinct organizational units and teams from HRIS."""
        employees = await self.fetch_employees()
        depts = sorted(list({e.get("dept_name") for e in employees if e.get("dept_name")}))
        return [{"dept_name": d, "headcount": sum(1 for e in employees if e.get("dept_name") == d)} for d in depts]

    async def fetch_roles(self) -> List[Dict[str, Any]]:
        """Fetch distinct job designations from HRIS."""
        employees = await self.fetch_employees()
        roles = sorted(list({e.get("designation") for e in employees if e.get("designation")}))
        return [{"designation": r, "count": sum(1 for e in employees if e.get("designation") == r)} for r in roles]

    async def fetch_performance(self) -> List[Dict[str, Any]]:
        """Fetch performance & engagement metrics from HRIS appraisal system."""
        employees = await self.fetch_employees()
        return [
            {
                "emp_id": e["emp_id"],
                "performance_score": e.get("performance_score"),
                "engagement_score": e.get("engagement_score"),
                "manager_feedback": e.get("manager_feedback")
            }
            for e in employees
        ]

    async def fetch_skills(self) -> List[Dict[str, Any]]:
        """Fetch aggregated employee skill inventory from HRIS profile competencies."""
        employees = await self.fetch_employees()
        skills = set()
        for e in employees:
            raw_s = e.get("skills", "")
            for s in str(raw_s).split(","):
                if s.strip():
                    skills.add(s.strip())
        return [{"skill_name": s} for s in sorted(list(skills))]

    async def sync(self) -> List[Dict[str, Any]]:
        """Fetch master data stream for integration pipeline."""
        return await self.fetch_employees()

    async def disconnect(self) -> None:
        """Gracefully terminate open sessions with external HRIS."""
        self.is_connected = False
