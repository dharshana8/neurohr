from abc import ABC
from typing import Any, List, Dict
from app.integrations.utils.synthetic_data import generate_mock_erp_data

class MockERPConnector(ABC):
    """Mock ERP connector implementing the BaseConnector interface."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def authenticate(self, credentials: Dict[str, Any] | None = None) -> bool:
        # Simulate successful authentication for mock ERP
        return True

    async def test_connection(self) -> bool:
        return True

    async def fetch_employees(self) -> List[Dict[str, Any]]:
        # Return static demo employee data with ERP field names
        return generate_mock_erp_data(count=100)

    async def fetch_departments(self) -> List[Dict[str, Any]]:
        return []

    async def fetch_roles(self) -> List[Dict[str, Any]]:
        return []

    async def fetch_performance(self) -> List[Dict[str, Any]]:
        return []

    async def fetch_skills(self) -> List[Dict[str, Any]]:
        return []

    async def sync(self) -> List[Dict[str, Any]]:
        # Directly return fetched employees for sync service
        return await self.fetch_employees()

    async def disconnect(self) -> None:
        return None
