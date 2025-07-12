from fastapi import APIRouter, HTTPException, status
from typing import List
from dependency import get_db, get_current_user
from models.academic import ClassSchedule, Course
from schemas.academic import ClassScheduleCreate, ClassScheduleUpdate, ClassScheduleResponse

router = APIRouter(prefix="/class-schedules", tags=["Class Schedules"])


# Guest/Public endpoints
@router.get("/public", response_model=List[ClassScheduleResponse])
def get_public_class_schedules(
    db: get_db,
    program_id: int = None,
    semester: int = None,
    year: int = None,
    batch: str = None,
    day_of_week: str = None,
    room: str = None,
    skip: int = 0,
    limit: int = 100
):
    """Public endpoint for guests to view class schedules with filters"""
    query = db.query(ClassSchedule).filter(ClassSchedule.is_active == 1).offset(skip).limit(limit)
    
    # Join with Course to filter by program
    if program_id is not None:
        query = query.join(Course).filter(Course.program_id == program_id)
    
    if semester is not None:
        query = query.filter(ClassSchedule.semester == semester)
    if year is not None:
        query = query.filter(ClassSchedule.year == year)
    if batch is not None:
        query = query.filter(ClassSchedule.batch == batch)
    if day_of_week is not None:
        query = query.filter(ClassSchedule.day_of_week == day_of_week)
    if room is not None:
        query = query.filter(ClassSchedule.room.ilike(f"%{room}%"))
    
    schedules = query.all()
    return schedules


# Student/Faculty endpoints
@router.get("/my-schedule", response_model=List[ClassScheduleResponse])
def get_my_class_schedule(
    db: get_db, 
    current_user: get_current_user,
    day_of_week: str = None,
    semester: int = None,
    year: int = None
):
    """Get current user's class schedule (works for both students and faculty)"""
    from models.user import Student, Faculty
    
    # Check if user is a student
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if student:
        # Get student's program courses and their schedules
        student_programs = [program.id for program in student.programs]
        if not student_programs:
            return []
        
        query = db.query(ClassSchedule).join(Course).filter(
            Course.program_id.in_(student_programs),
            ClassSchedule.is_active == 1
        )
        
        # Filter by student's year and semester if available
        if student.year:
            query = query.filter(ClassSchedule.year == student.year)
        if student.semester:
            query = query.filter(ClassSchedule.semester == student.semester)
            
    else:
        # Check if user is faculty
        faculty = db.query(Faculty).filter(Faculty.user_id == current_user.id).first()
        if faculty:
            # Get faculty's teaching schedules
            query = db.query(ClassSchedule).join(Course).filter(
                Course.teacher_id == faculty.id,
                ClassSchedule.is_active == 1
            )
        else:
            return []
    
    # Apply additional filters
    if day_of_week is not None:
        query = query.filter(ClassSchedule.day_of_week == day_of_week)
    if semester is not None:
        query = query.filter(ClassSchedule.semester == semester)
    if year is not None:
        query = query.filter(ClassSchedule.year == year)
    
    schedules = query.all()
    return schedules


# Admin endpoints
@router.post("", response_model=ClassScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_class_schedule(schedule: ClassScheduleCreate, db: get_db, current_user: get_current_user):
    """Create a new class schedule (Admin only)"""
    # Check for time conflicts
    existing_schedule = db.query(ClassSchedule).filter(
        ClassSchedule.day_of_week == schedule.day_of_week,
        ClassSchedule.room == schedule.room,
        ClassSchedule.start_time == schedule.start_time,
        ClassSchedule.is_active == 1
    ).first()
    
    if existing_schedule:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Time slot conflict: Another class is scheduled at this time in the same room"
        )
    
    db_schedule = ClassSchedule(**schedule.model_dump())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule


@router.get("", response_model=List[ClassScheduleResponse])
def get_class_schedules(
    db: get_db, 
    current_user: get_current_user,
    course_id: int = None,
    semester: int = None,
    year: int = None,
    batch: str = None,
    day_of_week: str = None,
    room: str = None,
    skip: int = 0,
    limit: int = 100
):
    """Get all class schedules with filters (Admin/Faculty)"""
    query = db.query(ClassSchedule).offset(skip).limit(limit)
    
    if course_id is not None:
        query = query.filter(ClassSchedule.course_id == course_id)
    if semester is not None:
        query = query.filter(ClassSchedule.semester == semester)
    if year is not None:
        query = query.filter(ClassSchedule.year == year)
    if batch is not None:
        query = query.filter(ClassSchedule.batch == batch)
    if day_of_week is not None:
        query = query.filter(ClassSchedule.day_of_week == day_of_week)
    if room is not None:
        query = query.filter(ClassSchedule.room.ilike(f"%{room}%"))
    
    schedules = query.all()
    return schedules


@router.get("/{schedule_id}", response_model=ClassScheduleResponse)
def get_class_schedule(schedule_id: int, db: get_db, current_user: get_current_user):
    """Get a specific class schedule"""
    schedule = db.query(ClassSchedule).filter(ClassSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class schedule not found")
    return schedule


@router.put("/{schedule_id}", response_model=ClassScheduleResponse)
def update_class_schedule(schedule_id: int, schedule_update: ClassScheduleUpdate, db: get_db, current_user: get_current_user):
    """Update a class schedule (Admin only)"""
    schedule = db.query(ClassSchedule).filter(ClassSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class schedule not found")
    
    update_data = schedule_update.model_dump(exclude_unset=True)
    
    # Check for time conflicts if time/room is being updated
    if any(field in update_data for field in ['day_of_week', 'start_time', 'room']):
        day = update_data.get('day_of_week', schedule.day_of_week)
        time = update_data.get('start_time', schedule.start_time)
        room = update_data.get('room', schedule.room)
        
        existing_schedule = db.query(ClassSchedule).filter(
            ClassSchedule.day_of_week == day,
            ClassSchedule.room == room,
            ClassSchedule.start_time == time,
            ClassSchedule.id != schedule_id,
            ClassSchedule.is_active == 1
        ).first()
        
        if existing_schedule:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="Time slot conflict: Another class is scheduled at this time in the same room"
            )
    
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class_schedule(schedule_id: int, db: get_db, current_user: get_current_user):
    """Delete a class schedule (Admin only)"""
    schedule = db.query(ClassSchedule).filter(ClassSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class schedule not found")
    
    db.delete(schedule)
    db.commit()
