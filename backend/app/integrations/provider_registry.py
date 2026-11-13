"""Provider registry mapping provider identifiers to connector classes."""
from typing import Dict, Type

from app.integrations.hris.connector import MockHRISConnector
from app.integrations.erp.connector import MockERPConnector
from app.integrations.csv.connector import CSVConnector

PROVIDERS: Dict[str, Type] = {
    "demo_hris": MockHRISConnector,
    "demo_erp": MockERPConnector,
    "hris": MockHRISConnector,
    "erp": MockERPConnector,
    "csv": CSVConnector,
}

def get_connector(provider_name: str, **kwargs):
    normalized = (provider_name or "").lower().strip()
    connector_cls = PROVIDERS.get(normalized)
    if not connector_cls:
        if "erp" in normalized:
            connector_cls = MockERPConnector
        elif "hris" in normalized:
            connector_cls = MockHRISConnector
        elif "csv" in normalized:
            connector_cls = CSVConnector
        else:
            raise ValueError(f"Provider '{provider_name}' not found in registry")
    return connector_cls(**kwargs)
