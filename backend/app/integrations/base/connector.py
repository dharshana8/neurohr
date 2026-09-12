from abc import ABC, abstractmethod
from typing import Any, List, Dict

class BaseConnector(ABC):
    """Abstract base class for all integration connectors.
    Each concrete connector must implement these methods.
    """

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any] | None = None) -> bool:
        """Perform any required authentication.
        Returns True if successful.
        """
        raise NotImplementedError

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test whether the connector can communicate with the source.
        Returns True on success.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_employees(self) -> List[Dict[str, Any]]:
        """Fetch raw employee records from the source.
        Returns a list of dictionaries representing employee data.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_departments(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_roles(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_performance(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_skills(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def sync(self) -> List[Dict[str, Any]]:
        """High‑level sync operation.
        Usually calls fetch_* methods, normalizes data, and returns the normalized list.
        """
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Clean up any open connections/resources."""
        raise NotImplementedError
