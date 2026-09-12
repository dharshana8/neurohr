from abc import ABC, abstractmethod
from typing import Any, List, Dict
from app.integrations.utils.synthetic_data import generate_mock_hris_data

class MockHRISConnector(ABC):
    """Mock HRIS connector implementing the BaseConnector interface."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def authenticate(self, credentials: Dict[str, Any] | None = None) -> bool:
        # Simulate successful authentication
        return True

    async def test_connection(self) -> bool:
        # Always succeeds for mock
        return True

    async def fetch_employees(self) -> List[Dict[str, Any]]:
        # Return static demo employee data with HRIS field names
        return generate_mock_hris_data(count=100)

    async def fetch_departments(self) -> List[Dict[str, Any]]:
        return []

    async def fetch_roles(self) -> List[Dict[str, Any]]:
        return []

    async def fetch_performance(self) -> List[Dict[str, Any]]:
        return []

    async def fetch_skills(self) -> List[Dict[str, Any]]:
        return []

    async def sync(self) -> List[Dict[str, Any]]:
        # Not used directly; integration service will call fetch_* and normalize.
        return await self.fetch_employees()

    async def disconnect(self) -> None:
        return None
