from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel
from dependency import get_db, get_current_user
from models import Student, Program, Course, CourseWork, CourseWorkSubmission, SubmissionStatus
from schemas import StudentUpdate, StudentResponse
from schemas import StudentCourseworksResponse
from datetime import datetime

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=List[StudentResponse])
def get_students(db: get_db, current_user: get_current_user, skip: int = 0, limit: int = 100, year: int = None, semester: int = None):
    query = db.query(Student).offset(skip).limit(limit)
    
    if year is not None:
        query = query.filter(Student.year == year)
    if semester is not None:
        query = query.filter(Student.semester == semester)
    
    students = query.all()
    return students


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: get_db, current_user: get_current_user):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


@router.get("/registration/{registration_number}", response_model=StudentResponse)
def get_student_by_registration(registration_number: str, db: get_db, current_user: get_current_user):
    student = db.query(Student).filter(Student.registration_number == registration_number).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


@router.get("/user/{user_id}", response_model=StudentResponse)
def get_student_by_user_id(user_id: int, db: get_db, current_user: get_current_user):
    student = db.query(Student).filter(Student.user_id == user_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


@router.put("/user/{user_id}", response_model=StudentResponse)
def update_student(user_id: int, student_update: StudentUpdate, db: get_db, current_user: get_current_user):
    student = db.query(Student).filter(Student.user_id == user_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    
    update_data = student_update.model_dump(exclude_unset=True)
    
    # Check registration number uniqueness if updating
    if 'registration_number' in update_data:
        existing_student = db.query(Student).filter(
            Student.registration_number == update_data['registration_number'], 
            Student.id != student.id
        ).first()
        if existing_student:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Registration number already exists")
    
    # Handle user-related updates
    user_fields = ['username', 'phone', 'gender']
    user_update_data = {k: v for k, v in update_data.items() if k in user_fields}
    student_update_data = {k: v for k, v in update_data.items() if k not in user_fields}
    
    # Update student fields
    for field, value in student_update_data.items():
        setattr(student, field, value)
    
    # Update user fields if any
    if user_update_data:
        user = student.user
        for field, value in user_update_data.items():
            setattr(user, field, value)
    
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: get_db, current_user: get_current_user):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    
    db.delete(student)
    db.commit()


@router.post("/{student_id}/programs/{program_id}")
def add_student_to_program(student_id: int, program_id: int, db: get_db, current_user: get_current_user):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    
    if program in student.programs:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student already enrolled in this program")
    
    student.programs.append(program)
    db.commit()
    
    return {"message": "Student successfully added to program"}


@router.delete("/{student_id}/programs/{program_id}")
def remove_student_from_program(student_id: int, program_id: int, db: get_db, current_user: get_current_user):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    
    if program not in student.programs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not enrolled in this program")
    
    student.programs.remove(program)
    db.commit()
    
    return {"message": "Student successfully removed from program"}


@router.get("/{student_id}/programs")
def get_student_programs(student_id: int, db: get_db, current_user: get_current_user):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    
    return {"student_id": student_id, "programs": student.programs}


@router.get("/me/profile", response_model=StudentResponse)
def get_current_student_profile(db: get_db, current_user: get_current_user):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
    return student


@router.get("/{student_id}/courseworks", response_model=StudentCourseworksResponse)
def get_student_courseworks(student_id: int, db: get_db, current_user: get_current_user):
    """
    Get all coursework submissions for a student.
    If the student hasn't submitted coursework, create a new submission with pending status.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    
    # Get all courseworks for programs the student is enrolled in
    student_programs = [program.id for program in student.programs]
    if not student_programs:
        return StudentCourseworksResponse(student_id=student_id, submissions=[])
    
    # Get all courseworks from courses in student's programs
    courseworks = db.query(CourseWork).join(Course).filter(
        Course.program_id.in_(student_programs)
    ).all()
    
    if not courseworks:
        return StudentCourseworksResponse(student_id=student_id, submissions=[])
    
    # Get existing submissions for this student
    existing_submissions = db.query(CourseWorkSubmission).filter(
        CourseWorkSubmission.student_id == student_id
    ).all()
    
    # Create a map of coursework_id -> submission for quick lookup
    submission_map = {sub.coursework_id: sub for sub in existing_submissions}
    
    # List to store all submissions (existing + newly created)
    all_submissions = []
    new_submissions = []
    
    # Process each coursework
    for coursework in courseworks:
        if coursework.id in submission_map:
            # Submission already exists
            all_submissions.append(submission_map[coursework.id])
        else:
            # Create new submission with pending status
            new_submission = CourseWorkSubmission(
                coursework_id=coursework.id,
                student_id=student_id,
                submission_date=datetime.now().isoformat(),
                status=SubmissionStatus.PENDING
            )
            new_submissions.append(new_submission)
            all_submissions.append(new_submission)
    
    # Add all new submissions to the database
    if new_submissions:
        db.add_all(new_submissions)
        db.commit()
        
        # Refresh all new submissions to get their IDs
        for submission in new_submissions:
            db.refresh(submission)
    
    return StudentCourseworksResponse(student_id=student_id, submissions=all_submissions)