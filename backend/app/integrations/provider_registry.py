"""Provider registry mapping provider identifiers to connector classes."""
from typing import Dict, Type

from app.integrations.hris.connector import MockHRISConnector
from app.integrations.erp.connector import MockERPConnector
from app.integrations.csv.connector import CSVConnector

PROVIDERS: Dict[str, Type] = {
    "demo_hris": MockHRISConnector,
    "demo_erp": MockERPConnector,
    "csv": CSVConnector,
}

def get_connector(provider_name: str, **kwargs):
    connector_cls = PROVIDERS.get(provider_name)
    if not connector_cls:
        raise ValueError(f"Provider {provider_name} not found")
    return connector_cls(**kwargs)
