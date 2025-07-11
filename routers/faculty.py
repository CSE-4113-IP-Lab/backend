from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
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
    user_fields = ['username', 'email', 'phone', 'password', 'gender', 'role', 'is_verified']
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
