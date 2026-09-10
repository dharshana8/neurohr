import pandas as pd
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from io import StringIO
from datetime import datetime
import math
import re

from app.models.user import User
from app.models.employee import Employee
from app.models.attrition import AttritionPrediction
from app.schemas.workforce import EmployeeResponse, ImportSummaryResponse, WorkforceStatsResponse
from app.api.deps import get_current_active_user

router = APIRouter()

def get_org_id(org_link):
    if hasattr(org_link, "ref"):
        return org_link.ref.id
    if hasattr(org_link, "id"):
        return org_link.id
    return org_link

@router.post("/import", response_model=ImportSummaryResponse)
async def import_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    contents = await file.read()
    try:
        df = pd.read_csv(StringIO(contents.decode('utf-8')))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")

    required_columns = [
        "employee_id", "name", "department", "role", "joining_date",
        "experience", "salary", "performance_score", "engagement_score",
        "overtime", "skills", "promotion_history", "manager_feedback",
        "employment_status", "attrition"
    ]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required CSV columns: {', '.join(missing_cols)}"
        )

    org_id = get_org_id(current_user.organization_id)

    # Fetch existing IDs for current organization to ensure organization isolation & unique check
    existing_emps = await Employee.find({"organization_id.$id": org_id}).to_list()
    existing_db_ids = {emp.employee_id for emp in existing_emps}



    seen_batch_ids = set()
    new_employees = []
    errors = []
    total_rows = len(df)
    valid_rows = 0
    invalid_rows = 0

    for index, row in df.iterrows():
        row_num = index + 2  # 1-indexed header is row 1
        row_errors = []

        # 1. employee_id check
        emp_id_raw = row.get('employee_id')
        if pd.isnull(emp_id_raw) or str(emp_id_raw).strip() == '':
            row_errors.append(f"Row {row_num}: Missing employee_id")
        else:
            emp_id = str(emp_id_raw).strip()
            if emp_id in seen_batch_ids or emp_id in existing_db_ids:
                row_errors.append(f"Row {row_num}: Duplicate employee_id")
            else:
                seen_batch_ids.add(emp_id)

        # 2. name check
        name_raw = row.get('name')
        if pd.isnull(name_raw) or str(name_raw).strip() == '':
            row_errors.append(f"Row {row_num}: Missing required field name")
        else:
            name = str(name_raw).strip()

        # 3. department check
        dept_raw = row.get('department')
        if pd.isnull(dept_raw) or str(dept_raw).strip() == '':
            row_errors.append(f"Row {row_num}: Missing required field department")
        else:
            department = str(dept_raw).strip()

        # 4. role check
        role_raw = row.get('role')
        if pd.isnull(role_raw) or str(role_raw).strip() == '':
            row_errors.append(f"Row {row_num}: Missing required field role")
        else:
            role = str(role_raw).strip()

        # 5. joining_date check
        joining_date_val = None
        date_raw = row.get('joining_date')
        if pd.isnull(date_raw):
            row_errors.append(f"Row {row_num}: Invalid joining_date")
        else:
            try:
                dt = pd.to_datetime(date_raw)
                if pd.isnull(dt):
                    row_errors.append(f"Row {row_num}: Invalid joining_date")
                else:
                    joining_date_val = dt.to_pydatetime()
            except Exception:
                row_errors.append(f"Row {row_num}: Invalid joining_date")

        # 6. experience check (numeric)
        exp_raw = row.get('experience')
        try:
            experience_val = float(exp_raw)
            if math.isnan(experience_val):
                row_errors.append(f"Row {row_num}: Invalid experience")
        except Exception:
            row_errors.append(f"Row {row_num}: Invalid experience")

        # 7. salary check (numeric)
        sal_raw = row.get('salary')
        try:
            salary_val = float(sal_raw)
            if math.isnan(salary_val):
                row_errors.append(f"Row {row_num}: Invalid salary")
        except Exception:
            row_errors.append(f"Row {row_num}: Invalid salary")

        # 8. performance_score check (numeric)
        perf_raw = row.get('performance_score')
        try:
            perf_val = float(perf_raw)
            if math.isnan(perf_val):
                row_errors.append(f"Row {row_num}: Invalid performance_score")
        except Exception:
            row_errors.append(f"Row {row_num}: Invalid performance_score")

        # 9. engagement_score check (numeric)
        eng_raw = row.get('engagement_score')
        try:
            eng_val = float(eng_raw)
            if math.isnan(eng_val):
                row_errors.append(f"Row {row_num}: Invalid engagement_score")
        except Exception:
            row_errors.append(f"Row {row_num}: Invalid engagement_score")

        # 10. overtime check (numeric)
        ot_raw = row.get('overtime')
        try:
            ot_val = float(ot_raw)
            if math.isnan(ot_val):
                row_errors.append(f"Row {row_num}: Invalid overtime")
        except Exception:
            row_errors.append(f"Row {row_num}: Invalid overtime")

        # 11. promotion_history check (numeric)
        promo_raw = row.get('promotion_history')
        try:
            promo_val = int(promo_raw)
        except Exception:
            row_errors.append(f"Row {row_num}: Invalid promotion_history")

        # 12. attrition check (0 or 1)
        att_raw = row.get('attrition')
        try:
            attrition_val = int(att_raw)
            if attrition_val not in (0, 1):
                row_errors.append(f"Row {row_num}: Invalid attrition")
        except Exception:
            row_errors.append(f"Row {row_num}: Invalid attrition")

        if row_errors:
            errors.extend(row_errors)
            invalid_rows += 1
        else:
            org_ref = current_user.organization_id.to_ref() if hasattr(current_user.organization_id, "to_ref") else current_user.organization_id
            emp = Employee(
                organization_id=org_ref,
                employee_id=emp_id,
                name=name,
                department=department,
                role=role,
                joining_date=joining_date_val,
                experience=experience_val,
                salary=salary_val,
                performance_score=perf_val,
                engagement_score=eng_val,
                overtime=ot_val,
                skills=str(row.get('skills', '') if not pd.isnull(row.get('skills')) else ''),
                promotion_history=promo_val,
                manager_feedback=str(row.get('manager_feedback', '') if not pd.isnull(row.get('manager_feedback')) else ''),
                employment_status=str(row.get('employment_status', 'Active') if not pd.isnull(row.get('employment_status')) else 'Active'),
                attrition=attrition_val
            )
            new_employees.append(emp)
            valid_rows += 1


    if new_employees:
        await Employee.insert_many(new_employees)

    return ImportSummaryResponse(
        total_rows=total_rows,
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        imported_rows=len(new_employees),
        errors=errors
    )

@router.get("/employees", response_model=List[EmployeeResponse])
async def get_employees(
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user)
):
    org_id = get_org_id(current_user.organization_id)
    employees = await Employee.find({"organization_id.$id": org_id}).to_list()
    
    # Filter in memory
    filtered = []
    for e in employees:
        if search:
            s_lower = search.lower()
            if not (s_lower in e.name.lower() or s_lower in e.employee_id.lower() or s_lower in e.department.lower() or s_lower in e.role.lower()):
                continue
        if department and department.lower() != 'all':
            if e.department.lower() != department.lower():
                continue
        if role and role.lower() != 'all':
            if e.role.lower() != role.lower():
                continue
        filtered.append(e)

    return [
        EmployeeResponse(
            id=str(e.id),
            employee_id=e.employee_id,
            name=e.name,
            department=e.department,
            role=e.role,
            joining_date=e.joining_date,
            experience=e.experience,
            salary=e.salary,
            performance_score=e.performance_score,
            engagement_score=e.engagement_score,
            overtime=e.overtime,
            skills=e.skills,
            promotion_history=e.promotion_history,
            manager_feedback=e.manager_feedback,
            employment_status=e.employment_status,
            attrition=e.attrition
        ) for e in filtered
    ]

@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    current_user: User = Depends(get_current_active_user)
):
    org_id = get_org_id(current_user.organization_id)
    e = await Employee.find_one(
        {"organization_id.$id": org_id},
        Employee.employee_id == employee_id
    )
    if not e:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    return EmployeeResponse(
        id=str(e.id),
        employee_id=e.employee_id,
        name=e.name,
        department=e.department,
        role=e.role,
        joining_date=e.joining_date,
        experience=e.experience,
        salary=e.salary,
        performance_score=e.performance_score,
        engagement_score=e.engagement_score,
        overtime=e.overtime,
        skills=e.skills,
        promotion_history=e.promotion_history,
        manager_feedback=e.manager_feedback,
        employment_status=e.employment_status,
        attrition=e.attrition
    )

@router.get("/stats", response_model=WorkforceStatsResponse)
async def get_stats(current_user: User = Depends(get_current_active_user)):
    org_id = get_org_id(current_user.organization_id)
    employees = await Employee.find({"organization_id.$id": org_id}).to_list()
    total = len(employees)
    if total == 0:
        return WorkforceStatsResponse(
            total_employees=0,
            high_attrition_risk=0,
            avg_performance=0.0,
            avg_engagement=0.0
        )
    
    preds = await AttritionPrediction.find(
        {"organization_id.$id": org_id},
        AttritionPrediction.risk_level == "HIGH"
    ).to_list()
    
    high_risk_count = len(preds)
    avg_perf = sum(e.performance_score for e in employees) / total
    avg_eng = sum(e.engagement_score for e in employees) / total
    
    return WorkforceStatsResponse(
        total_employees=total,
        high_attrition_risk=high_risk_count,
        avg_performance=round(avg_perf, 2),
        avg_engagement=round(avg_eng, 2)
    )



