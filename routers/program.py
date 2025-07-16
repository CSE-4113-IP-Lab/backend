from fastapi import APIRouter, HTTPException, status
from typing import List
from dependency import get_db, get_current_user
from models.academic import Program
from models.user import Student
from schemas.academic import ProgramCreate, ProgramUpdate, ProgramResponse
from schemas.user import StudentResponse

router = APIRouter(prefix="/programs", tags=["Programs"])


# Guest/Public endpoints
@router.get("/public", response_model=List[ProgramResponse])
def get_public_programs(db: get_db, skip: int = 0, limit: int = 100):
    """Public endpoint for guests to view active programs"""
    programs = db.query(Program).filter(Program.is_active == 1).offset(skip).limit(limit).all()
    return programs


@router.get("/public/{program_id}", response_model=ProgramResponse)
def get_public_program(program_id: int, db: get_db):
    """Public endpoint for guests to view program details"""
    program = db.query(Program).filter(Program.id == program_id, Program.is_active == 1).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    return program


@router.get("/public/{program_id}/outline")
def get_program_outline(program_id: int, db: get_db):
    """Public endpoint to get degree outline with courses organized by semester/year"""
    from models.academic import Course
    
    program = db.query(Program).filter(Program.id == program_id, Program.is_active == 1).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    
    # Get all courses for this program
    courses = db.query(Course).filter(Course.program_id == program_id).all()
    
    # Organize courses by year and semester
    outline = {}
    for course in courses:
        year = course.year or 0
        semester = course.semester or 0
        
        if year not in outline:
            outline[year] = {}
        if semester not in outline[year]:
            outline[year][semester] = []
        
        outline[year][semester].append({
            "id": course.id,
            "name": course.name,
            "course_code": course.course_code,
            "credits": course.credits,
            "description": course.description,
            "batch": course.batch
        })
    
    return {
        "program": {
            "id": program.id,
            "name": program.name,
            "type": program.type,
            "duration": program.duration,
            "description": program.description
        },
        "outline": outline
    }


# Authenticated endpoints
@router.post("", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
def create_program(program: ProgramCreate, db: get_db, current_user: get_current_user):
    db_program = Program(**program.model_dump())
    db.add(db_program)
    db.commit()
    db.refresh(db_program)
    return db_program


@router.get("", response_model=List[ProgramResponse])
def get_programs(db: get_db, current_user: get_current_user):
    programs = db.query(Program).all()
    return programs

@router.get("/{program_id}/students", response_model=List[StudentResponse])
def get_program_students(program_id: int, db: get_db, current_user: get_current_user):
    """Get all students enrolled in a specific program"""
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    
    students = db.query(Student).join(Student.programs).filter(Program.id == program_id).all()
    return students


@router.get("/{program_id}", response_model=ProgramResponse)
def get_program(program_id: int, db: get_db, current_user: get_current_user):
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    return program


@router.put("/{program_id}", response_model=ProgramResponse)
def update_program(program_id: int, program_update: ProgramUpdate, db: get_db, current_user: get_current_user):
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    
    update_data = program_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(program, field, value)
    
    db.commit()
    db.refresh(program)
    return program


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_program(program_id: int, db: get_db, current_user: get_current_user):
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    
    db.delete(program)
    db.commit()
