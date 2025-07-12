from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional
from dependency import get_db, get_current_user
from models.user import Faculty, User
from models.academic import Program
from schemas.user import FacultyCreate, FacultyUpdate, FacultyResponse

router = APIRouter(prefix="/faculties", tags=["Faculties"])


@router.get("", response_model=List[FacultyResponse])
def get_faculties(db: get_db, current_user: get_current_user, skip: int = 0, limit: int = 100, designation: str = None):
    query = db.query(Faculty).offset(skip).limit(limit)
    
    if designation:
        query = query.filter(Faculty.designation.ilike(f"%{designation}%"))
    
    faculties = query.all()
    return faculties


@router.get("/{faculty_id}", response_model=FacultyResponse)
def get_faculty(faculty_id: int, db: get_db, current_user: get_current_user):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")
    return faculty


@router.get("/user/{user_id}", response_model=FacultyResponse)
def get_faculty_by_user_id(user_id: int, db: get_db, current_user: get_current_user):
    faculty = db.query(Faculty).filter(Faculty.user_id == user_id).first()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")
    return faculty

@router.put("/user/{user_id}", response_model=FacultyResponse)
def update_faculty(user_id: int, faculty_update: FacultyUpdate, db: get_db, current_user: get_current_user):
    faculty = db.query(Faculty).filter(Faculty.user_id == user_id).first()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")
    
    update_data = faculty_update.model_dump(exclude_unset=True)
    
    # Handle user-related updates
    user_fields = ['username', 'phone', 'gender']
    user_update_data = {k: v for k, v in update_data.items() if k in user_fields}
    faculty_update_data = {k: v for k, v in update_data.items() if k not in user_fields}
    
    # Update faculty fields
    for field, value in faculty_update_data.items():
        setattr(faculty, field, value)
    
    # Update user fields if any
    if user_update_data:
        user = faculty.user
        for field, value in user_update_data.items():
            setattr(user, field, value)
    
    db.commit()
    db.refresh(faculty)
    return faculty


@router.delete("/{faculty_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faculty(faculty_id: int, db: get_db, current_user: get_current_user):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")
    
    db.delete(faculty)
    db.commit()


@router.post("/{faculty_id}/programs/{program_id}")
def add_faculty_to_program(faculty_id: int, program_id: int, db: get_db, current_user: get_current_user):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")
    
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    
    if program in faculty.programs:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Faculty already assigned to this program")
    
    faculty.programs.append(program)
    db.commit()
    
    return {"message": "Faculty successfully assigned to program"}


@router.delete("/{faculty_id}/programs/{program_id}")
def remove_faculty_from_program(faculty_id: int, program_id: int, db: get_db, current_user: get_current_user):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")
    
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    
    if program not in faculty.programs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not assigned to this program")
    
    faculty.programs.remove(program)
    db.commit()
    
    return {"message": "Faculty successfully removed from program"}


@router.get("/{faculty_id}/programs")
def get_faculty_programs(faculty_id: int, db: get_db, current_user: get_current_user):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")
    
    return {"faculty_id": faculty_id, "programs": faculty.programs}


@router.get("/{faculty_id}/courses")
def get_faculty_courses(faculty_id: int, db: get_db, current_user: get_current_user):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")
    
    return {"faculty_id": faculty_id, "courses": faculty.courses}


@router.get("/me/profile", response_model=FacultyResponse)
def get_current_faculty_profile(db: get_db, current_user: get_current_user):
    faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty profile not found")
    return faculty


@router.get("/search", response_model=List[FacultyResponse])
def search_faculties(
    db: get_db, 
    current_user: get_current_user,
    designation: Optional[str] = Query(None, description="Filter by designation"),
    expertise: Optional[str] = Query(None, description="Filter by expertise area"),
    bio: Optional[str] = Query(None, description="Search in bio"),
    on_leave: Optional[bool] = Query(None, description="Filter by leave status"),
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return")
):
    """
    Search faculties based on various criteria:
    - designation: Filter by faculty designation
    - expertise: Search for specific expertise area
    - bio: Search in faculty bio
    - on_leave: Filter by leave status
    """
    query = db.query(Faculty)
    
    # Apply filters based on provided parameters
    if designation:
        query = query.filter(Faculty.designation.ilike(f"%{designation}%"))
    
    if expertise:
        # Search in JSON array for expertise
        query = query.filter(func.json_extract(Faculty.expertise, '$').like(f'%{expertise}%'))
    
    if bio:
        query = query.filter(Faculty.bio.ilike(f"%{bio}%"))
    
    if on_leave is not None:
        leave_value = 1 if on_leave else 0
        query = query.filter(Faculty.on_leave == leave_value)
    
    # Apply pagination
    faculties = query.offset(skip).limit(limit).all()
    
    return faculties


@router.get("/expertise/{expertise_area}", response_model=List[FacultyResponse])
def get_faculties_by_expertise(
    expertise_area: str,
    db: get_db,
    current_user: get_current_user,
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return")
):
    """
    Get all faculties who have a specific expertise area.
    This searches for exact or partial matches in the expertise array.
    """
    # Search for faculties with the specified expertise
    query = db.query(Faculty).filter(
        func.json_extract(Faculty.expertise, '$').like(f'%{expertise_area}%')
    )
    
    faculties = query.offset(skip).limit(limit).all()
    
    return faculties


@router.get("/expertise", response_model=List[str])
def get_all_expertise_areas(db: get_db, current_user: get_current_user):
    """
    Get all unique expertise areas from all faculties.
    """
    faculties = db.query(Faculty).filter(Faculty.expertise.isnot(None)).all()
    
    # Collect all expertise areas
    all_expertise = set()
    for faculty in faculties:
        if faculty.expertise:
            all_expertise.update(faculty.expertise)
    
    return sorted(list(all_expertise))
