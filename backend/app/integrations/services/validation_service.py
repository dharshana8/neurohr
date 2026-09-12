from app.integrations.base.schemas import NormalizedEmployee
from app.integrations.base.exceptions import IntegrationValidationError

def validate_employee(employee: NormalizedEmployee) -> None:
    """Validate a normalized employee before saving."""
    if employee.salary < 0:
        raise IntegrationValidationError(f"Invalid salary for employee {employee.employee_id}: {employee.salary}")
    if employee.experience < 0:
        raise IntegrationValidationError(f"Invalid experience for employee {employee.employee_id}: {employee.experience}")
    # Additional validations can be added here
