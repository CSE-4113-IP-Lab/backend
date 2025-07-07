from fastapi import APIRouter, HTTPException, status
from typing import List
from dependency import get_db, get_current_user
from models import Mark, Program, Course, Student
from models.user import User
from schemas import MarkCreate, MarkUpdate, MarkResponse, ProgramCGPAResponse, StudentCGPA

router = APIRouter(prefix="/marks", tags=["Marks"])


@router.post("", response_model=MarkResponse, status_code=status.HTTP_201_CREATED)
def create_mark(mark: MarkCreate, db: get_db, current_user: get_current_user):
    db_mark = Mark(**mark.model_dump())
    db.add(db_mark)
    db.commit()
    db.refresh(db_mark)
    return db_mark


@router.get("", response_model=List[MarkResponse])
def get_marks(db: get_db, current_user: get_current_user):
    marks = db.query(Mark).all()
    return marks


@router.get("/{mark_id}", response_model=MarkResponse)
def get_mark(mark_id: int, db: get_db, current_user: get_current_user):
    mark = db.query(Mark).filter(Mark.id == mark_id).first()
    if not mark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mark not found")
    return mark


@router.put("/{mark_id}", response_model=MarkResponse)
def update_mark(mark_id: int, mark_update: MarkUpdate, db: get_db, current_user: get_current_user):
    mark = db.query(Mark).filter(Mark.id == mark_id).first()
    if not mark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mark not found")
    
    update_data = mark_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mark, field, value)
    
    db.commit()
    db.refresh(mark)
    return mark


@router.delete("/{mark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mark(mark_id: int, db: get_db, current_user: get_current_user):
    mark = db.query(Mark).filter(Mark.id == mark_id).first()
    if not mark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mark not found")
    
    db.delete(mark)
    db.commit()


@router.get("/student/{student_id}", response_model=List[MarkResponse])
def get_marks_by_student(student_id: int, db: get_db, current_user: get_current_user):
    marks = db.query(Mark).filter(Mark.student_id == student_id).all()
    return marks


@router.get("/course/{course_id}", response_model=List[MarkResponse])
def get_marks_by_course(course_id: int, db: get_db, current_user: get_current_user):
    marks = db.query(Mark).filter(Mark.course_id == course_id).all()
    return marks


@router.get("/program/{program_id}/cgpa", response_model=ProgramCGPAResponse)
def calculate_program_cgpa(program_id: int, db: get_db, current_user: get_current_user):
    # Check if program exists
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    
    # Get all students in the program
    students_in_program = (
        db.query(Student)
        .join(Student.programs)
        .filter(Program.id == program_id)
        .all()
    )
    
    student_cgpas = []
    
    for student in students_in_program:
        # Get all courses for this program
        program_courses = db.query(Course).filter(Course.program_id == program_id).all()
        
        total_grade_points = 0
        total_credits = 0
        
        for course in program_courses:
            # Get all marks for this student in this specific course
            course_marks = (
                db.query(Mark)
                .filter(Mark.student_id == student.id)
                .filter(Mark.course_id == course.id)
                .all()
            )
            
            if not course_marks:
                continue  # Skip courses with no marks
            
            # Calculate total marks obtained and total possible marks for this course
            total_marks_obtained = 0
            total_possible_marks = 0
            
            for mark in course_marks:
                total_marks_obtained += mark.marks_obtained
                total_possible_marks += mark.total_marks
            
            if total_possible_marks == 0:
                continue  # Skip if no total marks
            
            # Calculate percentage for this course
            percentage = (total_marks_obtained / total_possible_marks) * 100
            
            if percentage >= 80:
                grade_point = 4.0
            elif percentage >= 75:
                grade_point = 3.75
            elif percentage >= 70:
                grade_point = 3.5
            elif percentage >= 65:
                grade_point = 3.25
            elif percentage >= 60:
                grade_point = 3.0
            elif percentage >= 55:
                grade_point = 2.75
            elif percentage >= 50:
                grade_point = 2.5
            elif percentage >= 45:
                grade_point = 2.25
            elif percentage >= 40:
                grade_point = 2.0
            else:
                grade_point = 0.0

            total_grade_points += grade_point * course.credits
            total_credits += course.credits
        
        # Calculate CGPA
        cgpa = total_grade_points / total_credits if total_credits > 0 else 0.0
        
        # Get student user info
        student_user = db.query(User).filter(User.id == student.user_id).first()
        student_name = student_user.username if student_user else "Unknown"
        
        student_cgpa = StudentCGPA(
            student_id=student.id,
            student_name=student_name,
            registration_number=student.registration_number,
            cgpa=round(cgpa, 2),
            total_credits=total_credits
        )
        student_cgpas.append(student_cgpa)
    
    return ProgramCGPAResponse(
        program_id=program.id,
        program_name=program.name,
        students=student_cgpas
    )
