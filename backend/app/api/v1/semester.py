from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.semester import semester as crud_semester
from app.schemas.semester import Semester, SemesterCreate, SemesterUpdate
from app.schemas.common import SuccessResponse
from app.db.session import get_db
from app.api.v1.auth import get_current_active_user # Assuming this dependency is available
from app.models.user import User

router = APIRouter()

@router.post("/semesters", response_model=SuccessResponse[Dict[str, Semester]], status_code=status.HTTP_201_CREATED)
def create_semester(
    *, 
    db: Session = Depends(get_db),
    semester_in: SemesterCreate,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Create a new semester."""
    # Only admin can create semesters for now, or specific roles
    # if current_user.role != "admin":
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    # Check if semester code already exists
    existing_semester = db.query(crud_semester.model).filter(crud_semester.model.code == semester_in.code).first()
    if existing_semester:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Semester with this code already exists")

    semester = crud_semester.create(db, obj_in=semester_in)
    return {"success": True, "data": {"semester": semester}}

@router.get("/semesters", response_model=SuccessResponse[Dict[str, List[Semester]]])
def read_semesters(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Retrieve semesters."""
    semesters = crud_semester.get_multi(db, skip=skip, limit=limit)
    return {"success": True, "data": {"semesters": semesters}}

@router.get("/semesters/{semester_id}", response_model=SuccessResponse[Dict[str, Semester]])
def read_semester_by_id(
    *, 
    db: Session = Depends(get_db),
    semester_id: int,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get a specific semester by ID."""
    semester = crud_semester.get(db, id=semester_id)
    if not semester:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found")
    return {"success": True, "data": {"semester": semester}}

@router.put("/semesters/{semester_id}", response_model=SuccessResponse[Dict[str, Semester]])
def update_semester(
    *, 
    db: Session = Depends(get_db),
    semester_id: int,
    semester_in: SemesterUpdate,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Update a semester."""
    semester = crud_semester.get(db, id=semester_id)
    if not semester:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found")
    
    # Only admin can update semesters for now, or specific roles
    # if current_user.role != "admin":
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    semester = crud_semester.update(db, db_obj=semester, obj_in=semester_in)
    return {"success": True, "data": {"semester": semester}}

@router.delete("/semesters/{semester_id}", response_model=SuccessResponse[Dict[str, Semester]])
def delete_semester(
    *, 
    db: Session = Depends(get_db),
    semester_id: int,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Delete a semester."""
    semester = crud_semester.get(db, id=semester_id)
    if not semester:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found")
    
    # Only admin can delete semesters for now, or specific roles
    # if current_user.role != "admin":
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    semester = crud_semester.remove(db, id=semester_id)
    return {"success": True, "data": {"semester": semester}}
