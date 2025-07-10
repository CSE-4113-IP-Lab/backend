from fastapi import APIRouter, HTTPException, status
from typing import List
from dependency import get_db, get_current_user
from models.academic import Course
from schemas.academic import CourseCreate, CourseUpdate, CourseResponse

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate, db: get_db, current_user: get_current_user):
    db_course = Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


@router.get("", response_model=List[CourseResponse])
def get_courses(db: get_db, current_user: get_current_user):
    courses = db.query(Course).all()
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
