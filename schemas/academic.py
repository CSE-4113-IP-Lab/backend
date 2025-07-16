from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime as DateTime
from models import ProgramType, SubmissionStatus, MarkType, DayOfWeek
from schemas import FileBase, FacultyResponse, StudentResponse


# Program schemas
class ProgramBase(BaseModel):
    type: ProgramType
    name: str
    duration: int
    description: Optional[str] = None
    is_active: Optional[int] = 1


class ProgramCreate(ProgramBase):
    pass


class ProgramUpdate(BaseModel):
    type: Optional[ProgramType] = None
    name: Optional[str] = None
    duration: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[int] = None


class ProgramResponse(ProgramBase):
    id: int

    class Config:
        from_attributes = True


# Course schemas
class CourseBase(BaseModel):
    name: str
    course_code: Optional[str] = None
    program_id: int
    teacher_id: Optional[int] = None
    credits: int
    description: Optional[str] = None
    semester: Optional[int] = None
    year: Optional[int] = None
    batch: Optional[str] = None


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    course_code: Optional[str] = None
    program_id: Optional[int] = None
    teacher_id: Optional[int] = None
    credits: Optional[int] = None
    description: Optional[str] = None
    semester: Optional[int] = None
    year: Optional[int] = None
    batch: Optional[str] = None


class CourseResponse(CourseBase):
    id: int

    class Config:
        from_attributes = True


# CourseWork schemas
class CourseWorkBase(BaseModel):
    course_id: int
    title: str
    type: str
    description: Optional[str] = None
    requirements : Optional[str] = None
    due_date: DateTime
    marks: Optional[float] = None


class CourseWorkCreate(CourseWorkBase):
    pass

class CourseWorkUpdate(BaseModel):
    course_id: Optional[int] = None
    title: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[DateTime] = None
    marks: Optional[float] = None


class CourseWorkResponse(CourseWorkBase):
    id: int
    created_by: int
    creator: Optional[FacultyResponse] = None
    course: Optional[CourseBase] = None
    created_at: DateTime
    updated_at: DateTime
    attachments: List[FileBase] = []

    class Config:
        from_attributes = True


# CourseWorkSubmission schemas
class CourseWorkSubmissionBase(BaseModel):
    id: int 
    coursework_id: int
    student_id: int
    submission_date: str
    status: Optional[SubmissionStatus] = SubmissionStatus.PENDING
    obtained_marks: Optional[float] = None
    feedback: Optional[str] = None


class CourseWorkSubmissionCreate(BaseModel):
    coursework_id: int
    student_id: int
    

class CourseWorkSubmissionWithAttachments(CourseWorkSubmissionBase):
    attachments: List[FileBase] = []

    class Config:
        from_attributes = True



class CourseWorkSubmissionUpdate(BaseModel):
    submission_date: Optional[str] = None
    status: Optional[SubmissionStatus] = None
    obtained_marks: Optional[float] = None
    feedback: Optional[str] = None


class CourseWorkSubmissionResponse(CourseWorkSubmissionBase):
    student: Optional[StudentResponse] = None
    coursework: Optional[CourseWorkResponse] = None
    attachments: List[FileBase] = []

    class Config:
        from_attributes = True

# Custom response model for student courseworks
class StudentCourseWorksResponse(CourseWorkBase):
    id: int
    course: Optional[CourseBase] = None
    submission: Optional[CourseWorkSubmissionWithAttachments] = None
    creator: Optional[FacultyResponse] = None
    created_at: DateTime
    updated_at: DateTime
    class Config:
        from_attributes = True
   


# Mark schemas
class MarkBase(BaseModel):
    student_id: int
    course_id: int
    type: MarkType
    marks_obtained: int
    total_marks: int


class MarkCreate(MarkBase):
    pass


class MarkUpdate(BaseModel):
    student_id: Optional[int] = None
    course_id: Optional[int] = None
    type: Optional[MarkType] = None
    marks_obtained: Optional[int] = None
    total_marks: Optional[int] = None


class MarkResponse(MarkBase):
    id: int
    student: Optional[StudentResponse] = None

    class Config:
        from_attributes = True


# CGPA calculation response
class StudentCGPA(BaseModel):
    student_id: int
    student_name: str
    registration_number: Optional[str] = None
    cgpa: float
    total_credits: int

    class Config:
        from_attributes = True


class ProgramCGPAResponse(BaseModel):
    program_id: int
    program_name: str
    students: List[StudentCGPA] = []

    class Config:
        from_attributes = True


# ClassSchedule schemas
class ClassScheduleBase(BaseModel):
    course_id: int
    day_of_week: DayOfWeek
    start_time: str  # Format: "HH:MM"
    end_time: str    # Format: "HH:MM"
    room: Optional[str] = None
    batch: Optional[str] = None
    semester: Optional[int] = None
    year: Optional[int] = None
    is_active: Optional[int] = 1


class ClassScheduleCreate(ClassScheduleBase):
    pass


class ClassScheduleUpdate(BaseModel):
    course_id: Optional[int] = None
    day_of_week: Optional[DayOfWeek] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    room: Optional[str] = None
    batch: Optional[str] = None
    semester: Optional[int] = None
    year: Optional[int] = None
    is_active: Optional[int] = None


class ClassScheduleResponse(ClassScheduleBase):
    id: int
    course: Optional[CourseResponse] = None

    class Config:
        from_attributes = True


# ExamSchedule schemas
class ExamScheduleBase(BaseModel):
    course_id: int
    exam_date: DateTime
    type: str  # e.g., "Midterm", "Final"
    start_time: str  # Format: "HH:MM"
    end_time: str    # Format: "HH:MM"
    room: Optional[str] = None
    batch: Optional[str] = None
    semester: Optional[int] = None
    year: Optional[int] = None


class ExamScheduleCreate(ExamScheduleBase):
    pass


class ExamScheduleUpdate(BaseModel):
    course_id: Optional[int] = None
    exam_date: Optional[DateTime] = None
    type: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    room: Optional[str] = None
    batch: Optional[str] = None
    semester: Optional[int] = None
    year: Optional[int] = None


class ExamScheduleResponse(ExamScheduleBase):
    id: int
    course: Optional[CourseResponse] = None

    class Config:
        from_attributes = True

