from typing import List, Dict, Any, Type
from app.integrations.models.integration import Integration
from app.integrations.models.sync_log import SyncLog
from app.integrations.provider_registry import get_connector
from app.integrations.services.validation_service import validate_employee
from app.integrations.hris.mapper import map_hris_row
from app.integrations.erp.mapper import map_erp_row
from app.models.employee import Employee
from app.integrations.base.exceptions import IntegrationValidationError
import datetime
from bson import ObjectId

class SyncService:
    @staticmethod
    async def sync_integration(integration: Integration) -> SyncLog:
        connector = get_connector(integration.provider_name)
        
        sync_log = SyncLog(
            organization_id=integration.organization_id,
            integration_id=str(integration.id),
            records_fetched=0,
            records_created=0,
            records_updated=0,
            status="Running",
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        await sync_log.insert()

        try:
            raw_employees = await connector.fetch_employees()
            sync_log.records_fetched = len(raw_employees)
            
            new_employees = []
            errors = []
            
            existing = await Employee.find({"organization_id.$id": integration.organization_id}).to_list()
            existing_ids = {e.employee_id: e for e in existing}

            mapper = map_hris_row if integration.provider_type == "hris" else map_erp_row
            
            for raw_row in raw_employees:
                try:
                    normalized_emp = mapper(raw_row)
                    validate_employee(normalized_emp)
                    
                    # Map to Employee model
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
                        skills=",".join(normalized_emp.skills) if normalized_emp.skills else "",
                        promotion_history=normalized_emp.promotion_history,
                        manager_feedback=normalized_emp.manager_feedback,
                        employment_status=normalized_emp.employment_status,
                        attrition=normalized_emp.attrition
                    )
                    
                    if emp_doc.employee_id in existing_ids:
                        # For simplicity, we just count as fetched, real upsert would update.
                        # We will skip update logic for demo and just count
                        pass
                    else:
                        new_employees.append(emp_doc)
                        
                except Exception as e:
                    errors.append(str(e))
            
            if new_employees:
                await Employee.insert_many(new_employees)
                sync_log.records_created = len(new_employees)
            
            sync_log.status = "Success"
            if errors:
                sync_log.message = f"Completed with {len(errors)} errors"
            else:
                sync_log.message = "Sync completed successfully"
                
            integration.last_sync_at = datetime.datetime.utcnow()
            await integration.save()
            
        except Exception as e:
            sync_log.status = "Failed"
            sync_log.message = str(e)
        
        sync_log.updated_at = datetime.datetime.utcnow()
        await sync_log.save()
        
        return sync_log
