from typing import Any, List, Dict, Optional
from app.integrations.base.connector import BaseConnector
from app.integrations.utils.synthetic_data import generate_mock_erp_data

class MockERPConnector(BaseConnector):
    """
    Mock enterprise ERP connector simulating external systems like SAP, Oracle ERP, or Microsoft Dynamics.
    Exposes raw ERP schemas through structured extraction methods.
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.is_connected = True
        self._cached_employees: Optional[List[Dict[str, Any]]] = None

    async def authenticate(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Simulate secure authentication handshake with external ERP service."""
        self.is_connected = True
        return True

    async def test_connection(self) -> bool:
        """Verify API connectivity and endpoint availability against external ERP."""
        return True

    async def fetch_employees(self) -> List[Dict[str, Any]]:
        """Fetch raw workforce master records from external ERP API."""
        if not self._cached_employees:
            self._cached_employees = generate_mock_erp_data(count=100)
        return self._cached_employees

    async def fetch_departments(self) -> List[Dict[str, Any]]:
        """Fetch distinct organizational department entities from ERP."""
        employees = await self.fetch_employees()
        depts = sorted(list({e.get("department_name") for e in employees if e.get("department_name")}))
        return [{"department_name": d, "headcount": sum(1 for e in employees if e.get("department_name") == d)} for d in depts]

    async def fetch_roles(self) -> List[Dict[str, Any]]:
        """Fetch distinct job titles and positions from ERP."""
        employees = await self.fetch_employees()
        roles = sorted(list({e.get("job_title") for e in employees if e.get("job_title")}))
        return [{"job_title": r, "count": sum(1 for e in employees if e.get("job_title") == r)} for r in roles]

    async def fetch_performance(self) -> List[Dict[str, Any]]:
        """Fetch employee performance rating records from ERP evaluation module."""
        employees = await self.fetch_employees()
        return [
            {"employee_code": e["employee_code"], "perf_rating": e.get("perf_rating"), "feedback": e.get("feedback")}
            for e in employees
        ]

    async def fetch_skills(self) -> List[Dict[str, Any]]:
        """Fetch aggregated skill competencies catalog from ERP."""
        employees = await self.fetch_employees()
        skills = set()
        for e in employees:
            raw_s = e.get("skill_set", "")
            for s in str(raw_s).split(","):
                if s.strip():
                    skills.add(s.strip())
        return [{"skill_name": s} for s in sorted(list(skills))]

    async def sync(self) -> List[Dict[str, Any]]:
        """Fetch master data stream for integration pipeline."""
        return await self.fetch_employees()

    async def disconnect(self) -> None:
        """Gracefully terminate open sessions with external ERP."""
        self.is_connected = False
