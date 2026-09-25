from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from bson import ObjectId

from app.integrations.models.integration import Integration
from app.integrations.models.data_mapping import DataMapping
from app.integrations.models.sync_log import SyncLog
from app.integrations.provider_registry import get_connector
from app.integrations.services.validation_service import validate_employee
from app.integrations.hris.mapper import map_hris_row
from app.integrations.erp.mapper import map_erp_row
from app.models.employee import Employee
from app.integrations.base.exceptions import IntegrationValidationError

def _resolve_org_id(org_link_or_id: Any) -> Any:
    if hasattr(org_link_or_id, "to_ref"):
        return org_link_or_id.to_ref().id
    if hasattr(org_link_or_id, "ref"):
        return org_link_or_id.ref.id
    if hasattr(org_link_or_id, "id"):
        return org_link_or_id.id
    if isinstance(org_link_or_id, str) and ObjectId.is_valid(org_link_or_id):
        return ObjectId(org_link_or_id)
    return org_link_or_id

def _org_filter(organization_id: Any) -> dict:
    resolved = _resolve_org_id(organization_id)
    conditions = [
        {"organization_id": resolved},
        {"organization_id.$id": resolved}
    ]
    if isinstance(resolved, ObjectId):
        conditions.extend([
            {"organization_id": str(resolved)},
            {"organization_id.$id": str(resolved)}
        ])
    elif isinstance(resolved, str) and ObjectId.is_valid(resolved):
        oid = ObjectId(resolved)
        conditions.extend([
            {"organization_id": oid},
            {"organization_id.$id": oid}
        ])
    return {"$or": conditions}

class SyncService:
    @staticmethod
    async def sync_integration(integration: Integration) -> SyncLog:
        """
        Executes a real synchronization pipeline:
        1. Validates connection state
        2. Fetches raw records from connector
        3. Applies configured DataMapping & normalization
        4. Validates field constraints
        5. Upserts employees into MongoDB with duplicate prevention
        6. Logs execution metrics into SyncLog
        """
        now = datetime.now(timezone.utc)
        resolved_org = _resolve_org_id(integration.organization_id)

        sync_log = SyncLog(
            organization_id=integration.organization_id,
            integration_id=integration.integration_id,
            started_at=now,
            status="IN_PROGRESS",
            records_fetched=0,
            records_created=0,
            records_updated=0,
            records_failed=0,
            created_at=now,
            updated_at=now
        )
        await sync_log.insert()

        if integration.status == "Disconnected":
            sync_log.status = "FAILED"
            sync_log.error_message = "Cannot synchronize a disconnected integration. Please connect first."
            sync_log.message = sync_log.error_message
            sync_log.completed_at = datetime.now(timezone.utc)
            sync_log.updated_at = sync_log.completed_at
            await sync_log.save()
            return sync_log

        try:
            connector = get_connector(integration.provider_name)
            raw_employees = await connector.fetch_employees()
            sync_log.records_fetched = len(raw_employees)

            # Retrieve active custom mappings from database if configured
            mappings_docs = await DataMapping.find({
                "$and": [
                    _org_filter(integration.organization_id),
                    {"integration_id": integration.integration_id},
                    {"mapping_status": "ACTIVE"}
                ]
            }).to_list()
            custom_mappings = {m.source_field: m.target_field for m in mappings_docs} if mappings_docs else None

            p_name = (integration.provider_name or "").lower()
            p_type = (integration.provider_type or "").lower()
            is_hris = ("hris" in p_name or "hris" in p_type)

            # Query existing employees for tenant to perform true upserts without duplication
            existing_employees = await Employee.find(_org_filter(integration.organization_id)).to_list()
            existing_map = {e.employee_id: e for e in existing_employees}

            records_created = 0
            records_updated = 0
            records_failed = 0
            details: List[str] = []

            for raw_row in raw_employees:
                try:
                    if is_hris:
                        normalized_emp = map_hris_row(raw_row, custom_mappings)
                    else:
                        normalized_emp = map_erp_row(raw_row, custom_mappings)

                    # Validate record according to normalization constraints
                    validate_employee(normalized_emp)

                    skills_str = ", ".join(normalized_emp.skills) if isinstance(normalized_emp.skills, list) else str(normalized_emp.skills or "")

                    if normalized_emp.employee_id in existing_map:
                        # Existing employee: update in-place (no duplicate creation!)
                        existing_emp = existing_map[normalized_emp.employee_id]
                        existing_emp.name = normalized_emp.name
                        existing_emp.department = normalized_emp.department
                        existing_emp.role = normalized_emp.role
                        existing_emp.joining_date = normalized_emp.joining_date
                        existing_emp.experience = normalized_emp.experience
                        existing_emp.salary = normalized_emp.salary
                        existing_emp.performance_score = normalized_emp.performance_score
                        existing_emp.engagement_score = normalized_emp.engagement_score
                        existing_emp.overtime = normalized_emp.overtime
                        existing_emp.skills = skills_str
                        existing_emp.promotion_history = normalized_emp.promotion_history
                        existing_emp.manager_feedback = normalized_emp.manager_feedback
                        existing_emp.employment_status = normalized_emp.employment_status
                        existing_emp.attrition = normalized_emp.attrition
                        await existing_emp.save()
                        records_updated += 1
                    else:
                        # New employee: insert
                        emp_doc = Employee(
                            organization_id=integration.organization_id,
                            employee_id=normalized_emp.employee_id,
                            name=normalized_emp.name,
                            department=normalized_emp.department,
                            role=normalized_emp.role,
                            joining_date=normalized_emp.joining_date,
                            experience=normalized_emp.experience,
                            salary=normalized_emp.salary,
                            performance_score=normalized_emp.performance_score,
                            engagement_score=normalized_emp.engagement_score,
                            overtime=normalized_emp.overtime,
                            skills=skills_str,
                            promotion_history=normalized_emp.promotion_history,
                            manager_feedback=normalized_emp.manager_feedback,
                            employment_status=normalized_emp.employment_status,
                            attrition=normalized_emp.attrition
                        )
                        await emp_doc.insert()
                        existing_map[emp_doc.employee_id] = emp_doc
                        records_created += 1

                except Exception as row_err:
                    records_failed += 1
                    code = raw_row.get("employee_code") or raw_row.get("emp_id") or "UNKNOWN"
                    details.append(f"Row {code} error: {str(row_err)}")

            sync_log.records_created = records_created
            sync_log.records_updated = records_updated
            sync_log.records_failed = records_failed
            sync_log.details = details[:25]  # Capture up to 25 failure explanations

            if records_failed > 0 and (records_created + records_updated) > 0:
                sync_log.status = "COMPLETED_WITH_ERRORS"
                sync_log.message = f"Sync completed with {records_failed} failed records"
            elif records_failed > 0 and (records_created + records_updated) == 0:
                sync_log.status = "FAILED"
                sync_log.error_message = f"Sync failed for all {records_failed} records: {details[0] if details else 'Validation failure'}"
                sync_log.message = sync_log.error_message
            else:
                sync_log.status = "SUCCESS"
                sync_log.message = f"Sync completed successfully. Created: {records_created}, Updated: {records_updated}."

            integration.last_sync_at = datetime.now(timezone.utc)
            await integration.save()

        except Exception as e:
            sync_log.status = "FAILED"
            sync_log.error_message = str(e)
            sync_log.message = str(e)

        sync_log.completed_at = datetime.now(timezone.utc)
        sync_log.updated_at = sync_log.completed_at
        await sync_log.save()
        return sync_log
