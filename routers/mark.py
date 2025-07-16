from fastapi import APIRouter, HTTPException, UploadFile, status
from typing import List
from dependency import get_db, get_current_user
from models import Mark, Program, Course, Student
from models import User
from models import MarkType
import csv
import io
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

@router.get("/course/{course_id}", response_model=List[MarkResponse])
def get_course_marks(course_id: int, db: get_db, current_user: get_current_user):

    marks = db.query(Mark).filter(Mark.course_id == course_id).all()

    return marks

@router.get("/course/{course_id}/student/{student_id}", response_model=List[MarkResponse])
def get_course_marks_by_student(course_id: int, student_id: int, db: get_db, current_user: get_current_user):
    """Get marks for a specific student in a specific course.
    """
    marks = db.query(Mark).filter(
        Mark.course_id == course_id,
        Mark.student_id == student_id
    ).all()
    
    return marks

@router.post("/course/{course_id}/csv")
def upload_course_marks_csv(course_id: int, incourse: int, final: int, other: int, file: UploadFile, db: get_db, current_user: get_current_user):
    """
    Upload marks for a course via CSV file.
    
    CSV should have columns: register_number, incourse, final, other
    Query parameters specify the total marks for each type.
    """
    # Check if course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV")
    
    try:
        # Read CSV content
        content = file.file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content))
        
        created_marks = []
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (header is row 1)
            try:
                register_number = row.get('register_number', '').strip()
                incourse_marks = row.get('incourse', '').strip()
                final_marks = row.get('final', '').strip()
                other_marks = row.get('other', '').strip()
                
                # Validate required fields
                if not register_number:
                    errors.append(f"Row {row_num}: Missing register_number")
                    continue
                
                # Find student by registration number
                student = db.query(Student).filter(Student.registration_number == register_number).first()
                if not student:
                    errors.append(f"Row {row_num}: Student with registration number '{register_number}' not found")
                    continue
                
                # Check if student is enrolled in this course's program
                course_program = course.program
                if course_program not in student.programs:
                    errors.append(f"Row {row_num}: Student '{register_number}' is not enrolled in the program for this course")
                    continue
                
                # Delete existing marks for this student and course
                existing_marks = db.query(Mark).filter(
                    Mark.student_id == student.id,
                    Mark.course_id == course_id
                ).all()
                for existing_mark in existing_marks:
                    db.delete(existing_mark)
                
                # Create marks for each type if provided
                marks_data = [
                    (MarkType.INCOURSE, incourse_marks, incourse),
                    (MarkType.FINAL, final_marks, final),
                    (MarkType.OTHER, other_marks, other)
                ]
                
                for mark_type, obtained_str, total_marks in marks_data:
                    if obtained_str:  # Only create mark if value is provided
                        try:
                            obtained_marks = float(obtained_str)
                            if obtained_marks < 0 or obtained_marks > total_marks:
                                errors.append(f"Row {row_num}: {mark_type.value} marks ({obtained_marks}) must be between 0 and {total_marks}")
                                continue
                            
                            # Create mark entry
                            mark = Mark(
                                student_id=student.id,
                                course_id=course_id,
                                type=mark_type,  # Use enum object directly
                                marks_obtained=int(obtained_marks),
                                total_marks=total_marks
                            )
                            db.add(mark)
                            created_marks.append({
                                "student_id": student.id,
                                "registration_number": register_number,
                                "type": mark_type.value,
                                "marks_obtained": int(obtained_marks),
                                "total_marks": total_marks
                            })
                        except ValueError:
                            errors.append(f"Row {row_num}: Invalid {mark_type.value} marks value '{obtained_str}'")
                            continue
                
            except Exception as e:
                errors.append(f"Row {row_num}: Error processing row - {str(e)}")
                continue
        
        db.commit()
        
        return {
            "message": "CSV processed successfully",
            "course_id": course_id,
            "course_name": course.name,
            "total_marks_created": len(created_marks),
            "created_marks": created_marks,
            "errors": errors,
            "total_errors": len(errors)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV file: {str(e)}"
        )
    finally:
        file.file.close()


