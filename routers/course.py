from fastapi import APIRouter, HTTPException, status
from typing import List
from dependency import get_db, get_current_user
from models.academic import Course
from schemas.academic import CourseCreate, CourseUpdate, CourseResponse

router = APIRouter(prefix="/courses", tags=["Courses"])


# Guest/Public endpoints (no authentication required)
@router.get("/public", response_model=List[CourseResponse])
def get_public_courses(
    db: get_db,
    program_id: int = None,
    semester: int = None,
    year: int = None,
    batch: str = None,
    skip: int = 0,
    limit: int = 100
):
    """Public endpoint for guests to view courses with filters"""
    query = db.query(Course).offset(skip).limit(limit)
    
    if program_id is not None:
        query = query.filter(Course.program_id == program_id)
    if semester is not None:
        query = query.filter(Course.semester == semester)
    if year is not None:
        query = query.filter(Course.year == year)
    if batch is not None:
        query = query.filter(Course.batch == batch)
    
    courses = query.all()
    return courses


@router.get("/public/{course_id}", response_model=CourseResponse)
def get_public_course(course_id: int, db: get_db):
    """Public endpoint for guests to view course details"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


# Authenticated endpoints
@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate, db: get_db, current_user: get_current_user):
    db_course = Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


@router.get("", response_model=List[CourseResponse])
def get_courses(
    db: get_db, 
    current_user: get_current_user,
    program_id: int = None,
    semester: int = None,
    year: int = None,
    batch: str = None,
    teacher_id: int = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(Course).offset(skip).limit(limit)
    
    if program_id is not None:
        query = query.filter(Course.program_id == program_id)
    if semester is not None:
        query = query.filter(Course.semester == semester)
    if year is not None:
        query = query.filter(Course.year == year)
    if batch is not None:
        query = query.filter(Course.batch == batch)
    if teacher_id is not None:
        query = query.filter(Course.teacher_id == teacher_id)
    
    courses = query.all()
    return courses


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: int, db: get_db, current_user: get_current_user):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.put("/{course_id}", response_model=CourseResponse)
def update_course(course_id: int, course_update: CourseUpdate, db: get_db, current_user: get_current_user):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    
    update_data = course_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    
    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, db: get_db, current_user: get_current_user):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    
    db.delete(course)
    db.commit()
