from app.integrations.base.schemas import NormalizedEmployee
from app.integrations.base.exceptions import IntegrationValidationError
from datetime import datetime

VALID_STATUSES = {"active", "terminated", "on leave", "probation", "suspended", "resigned", "inactive"}

def validate_employee(employee: NormalizedEmployee) -> None:
    """
    Validate a normalized employee before persisting to the database.
    Raises IntegrationValidationError with detailed context on failures.
    """
    if not employee.employee_id or not employee.employee_id.strip():
        raise IntegrationValidationError("Missing required field: employee_id is blank or null")

    if not employee.name or not employee.name.strip():
        raise IntegrationValidationError(f"Missing required field: name is blank for employee_id '{employee.employee_id}'")

    if not employee.department or not employee.department.strip():
        raise IntegrationValidationError(f"Missing required field: department is blank for employee_id '{employee.employee_id}'")

    if not employee.role or not employee.role.strip():
        raise IntegrationValidationError(f"Missing required field: role is blank for employee_id '{employee.employee_id}'")

    if employee.salary <= 0:
        raise IntegrationValidationError(
            f"Invalid salary for employee '{employee.employee_id}': salary must be positive, got {employee.salary}"
        )

    if employee.experience < 0:
        raise IntegrationValidationError(
            f"Invalid experience for employee '{employee.employee_id}': experience cannot be negative, got {employee.experience}"
        )

    if not (1.0 <= employee.performance_score <= 5.0):
        raise IntegrationValidationError(
            f"Invalid performance score for employee '{employee.employee_id}': must be between 1.0 and 5.0, got {employee.performance_score}"
        )

    if employee.overtime < 0:
        raise IntegrationValidationError(
            f"Invalid overtime hours for employee '{employee.employee_id}': overtime cannot be negative, got {employee.overtime}"
        )

    if not isinstance(employee.joining_date, datetime):
        raise IntegrationValidationError(
            f"Invalid joining date for employee '{employee.employee_id}': expected datetime instance"
        )

    if employee.employment_status and employee.employment_status.strip().lower() not in VALID_STATUSES:
        raise IntegrationValidationError(
            f"Invalid employment status for employee '{employee.employee_id}': got '{employee.employment_status}'"
        )
