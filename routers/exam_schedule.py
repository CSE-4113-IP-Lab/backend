from fastapi import APIRouter, HTTPException, status
from typing import List
from dependency import get_db, get_current_user
from models.academic import ExamSchedule, Course
from schemas.academic import ExamScheduleCreate, ExamScheduleUpdate, ExamScheduleResponse
from datetime import datetime

router = APIRouter(prefix="/exam-schedules", tags=["Exam Schedules"])


# Guest/Public endpoints
@router.get("/public", response_model=List[ExamScheduleResponse])
def get_public_exam_schedules(
    db: get_db,
    program_id: int = None,
    semester: int = None,
    year: int = None,
    batch: str = None,
    type : str = None,
    exam_date: str = None,
    room: str = None,
    skip: int = 0,
    limit: int = 100
):
    """Public endpoint for guests to view exam schedules with filters"""
    query = db.query(ExamSchedule).offset(skip).limit(limit)
    
    # Join with Course to filter by program
    if program_id is not None:
        query = query.join(Course).filter(Course.program_id == program_id)
    
    if semester is not None:
        query = query.filter(ExamSchedule.semester == semester)
    if year is not None:
        query = query.filter(ExamSchedule.year == year)
    if batch is not None:
        query = query.filter(ExamSchedule.batch == batch)
    if type is not None:
        query = query.filter(ExamSchedule.type == type)
    if exam_date is not None:
        try:
            date_obj = datetime.strptime(exam_date, "%Y-%m-%d").date()
            query = query.filter(ExamSchedule.exam_date.date() == date_obj)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    if room is not None:
        query = query.filter(ExamSchedule.room.ilike(f"%{room}%"))
    
    schedules = query.all()
    return schedules


# Student/Faculty endpoints
@router.get("/my-schedule", response_model=List[ExamScheduleResponse])
def get_my_exam_schedule(
    db: get_db, 
    current_user: get_current_user,
    exam_date: str = None,
    semester: int = None,
    type: str = None,   
    year: int = None
):
    """Get current user's exam schedule (works for both students and faculty)"""
    from models.user import Student, Faculty
    
    # Check if user is a student
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if student:
        # Get student's program courses and their exam schedules
        student_programs = [program.id for program in student.programs]
        if not student_programs:
            return []
        
        query = db.query(ExamSchedule).join(Course).filter(
            Course.program_id.in_(student_programs)
        )
        
        # Filter by student's year and semester if available
        if student.year:
            query = query.filter(ExamSchedule.year == student.year)
        if student.semester:
            query = query.filter(ExamSchedule.semester == student.semester)
        if type is not None:
            query = query.filter(ExamSchedule.type == type)
            
    else:
        # Check if user is faculty
        faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
        if faculty:
            # Get faculty's exam schedules
            query = db.query(ExamSchedule).join(Course).filter(
                Course.teacher_id == faculty.id
            )
        else:
            return []
    
    # Apply additional filters
    if exam_date is not None:
        try:
            date_obj = datetime.strptime(exam_date, "%Y-%m-%d").date()
            query = query.filter(ExamSchedule.exam_date.date() == date_obj)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    if semester is not None:
        query = query.filter(ExamSchedule.semester == semester)
    if year is not None:
        query = query.filter(ExamSchedule.year == year)
    
    schedules = query.all()
    return schedules


# Admin endpoints
@router.post("", response_model=ExamScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_exam_schedule(schedule: ExamScheduleCreate, db: get_db, current_user: get_current_user):
    """Create a new exam schedule (Admin only)"""
    # Check for time conflicts
    existing_schedule = db.query(ExamSchedule).filter(
        ExamSchedule.exam_date == schedule.exam_date,
        ExamSchedule.room == schedule.room,
        ExamSchedule.start_time == schedule.start_time
    ).first()
    
    if existing_schedule:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Time slot conflict: Another exam is scheduled at this time in the same room"
        )
    
    db_schedule = ExamSchedule(**schedule.model_dump())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


@router.get("", response_model=List[ExamScheduleResponse])
def get_exam_schedules(
    db: get_db, 
    current_user: get_current_user,
    course_id: int = None,
    semester: int = None,
    year: int = None,
    batch: str = None,
    type: str = None,
    exam_date: str = None,
    room: str = None,
    skip: int = 0,
    limit: int = 100
):
    """Get all exam schedules with filters (Admin/Faculty)"""
    query = db.query(ExamSchedule).offset(skip).limit(limit)
    
    if course_id is not None:
        query = query.filter(ExamSchedule.course_id == course_id)
    if semester is not None:
        query = query.filter(ExamSchedule.semester == semester)
    if year is not None:
        query = query.filter(ExamSchedule.year == year)
    if batch is not None:
        query = query.filter(ExamSchedule.batch == batch)
    if type is not None:
        query = query.filter(ExamSchedule.type == type)
    if exam_date is not None:
        try:
            date_obj = datetime.strptime(exam_date, "%Y-%m-%d").date()
            query = query.filter(ExamSchedule.exam_date.date() == date_obj)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    if room is not None:
        query = query.filter(ExamSchedule.room.ilike(f"%{room}%"))
    
    schedules = query.all()
    return schedules


@router.get("/{schedule_id}", response_model=ExamScheduleResponse)
def get_exam_schedule(schedule_id: int, db: get_db, current_user: get_current_user):
    """Get a specific exam schedule"""
    schedule = db.query(ExamSchedule).filter(ExamSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam schedule not found")
    return schedule


@router.put("/{schedule_id}", response_model=ExamScheduleResponse)
def update_exam_schedule(schedule_id: int, schedule_update: ExamScheduleUpdate, db: get_db, current_user: get_current_user):
    """Update an exam schedule (Admin only)"""
    schedule = db.query(ExamSchedule).filter(ExamSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam schedule not found")
    
    update_data = schedule_update.model_dump(exclude_unset=True)
    
    # Check for time conflicts if date/time/room is being updated
    if any(field in update_data for field in ['exam_date', 'start_time', 'room']):
        date = update_data.get('exam_date', schedule.exam_date)
        time = update_data.get('start_time', schedule.start_time)
        room = update_data.get('room', schedule.room)
        
        existing_schedule = db.query(ExamSchedule).filter(
            ExamSchedule.exam_date == date,
            ExamSchedule.room == room,
            ExamSchedule.start_time == time,
            ExamSchedule.id != schedule_id
        ).first()
        
        if existing_schedule:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="Time slot conflict: Another exam is scheduled at this time in the same room"
            )
    
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam_schedule(schedule_id: int, db: get_db, current_user: get_current_user):
    """Delete an exam schedule (Admin only)"""
    schedule = db.query(ExamSchedule).filter(ExamSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam schedule not found")
    
    db.delete(schedule)
    db.commit()
