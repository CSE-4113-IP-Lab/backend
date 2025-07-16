from datetime import datetime
from models import Base
from models import student_programs, faculty_programs, coursework_files, coursework_submission_files
from sqlalchemy import Column, ForeignKey, Integer, String, Enum, DateTime, Float
from sqlalchemy.orm import relationship
from models import MarkType, ProgramType, SubmissionStatus, DayOfWeek


class Program(Base):
    __tablename__ = 'programs'
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(ProgramType), nullable=False)  # e.g., 'BSc', 'MSc', 'PhD'
    name = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)  # in years
    description = Column(String, nullable=True)

    is_active = Column(Integer, default=1) 

    courses = relationship("Course", back_populates="program")
    transactions = relationship("PaymentTransaction", back_populates="program")
    payment_fees = relationship("PaymentFee", back_populates="program")
    schedules = relationship("Schedule", back_populates="program")
    admission_timelines = relationship("AdmissionTimeline", back_populates="program")
    students = relationship("Student", secondary=student_programs, back_populates="programs")
    faculties = relationship("Faculty", secondary=faculty_programs, back_populates="programs")


class Course(Base):
    __tablename__ = 'courses'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    course_code = Column(String, unique=True, nullable=True)
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('faculties.id'), nullable=True)
    credits = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    semester = Column(Integer, nullable=True)  # Which semester (1-8)
    year = Column(Integer, nullable=True)  # Which year (1-4)
    batch = Column(String, nullable=True)  # Batch identifier

    teacher = relationship("Faculty", back_populates="courses")
    program = relationship("Program", back_populates="courses")
    courseworks = relationship("CourseWork", back_populates="course")
    marks = relationship("Mark", back_populates="course")
   


class Mark(Base):
    __tablename__ = 'marks'
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    type = Column(Enum(MarkType), nullable=False)
    marks_obtained = Column(Integer, nullable=False)
    total_marks = Column(Integer, nullable=False)

    student = relationship("Student", back_populates="marks")
    course = relationship("Course", back_populates="marks")


class CourseWork(Base):
    __tablename__ = 'courseworks'
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    created_by = Column(Integer, ForeignKey('faculties.id'), nullable=False)  
    due_date = Column(DateTime, nullable=False)
    requirements = Column(String, nullable=True, default='')
    marks = Column(Float, nullable=True) 

    attachments = relationship("File", secondary=coursework_files, overlaps="courseworks")
    course = relationship("Course", back_populates="courseworks")
    submissions = relationship("CourseWorkSubmission", back_populates="coursework")
    creator = relationship("Faculty")


class CourseWorkSubmission(Base):
    __tablename__ = 'coursework_submissions'
    
    id = Column(Integer, primary_key=True, index=True)
    coursework_id = Column(Integer, ForeignKey('courseworks.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    submission_date = Column(String, nullable=False, default=datetime.now())  
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING) 

    obtained_marks = Column(Float, nullable=True)   
    feedback = Column(String, nullable=True)  

    attachments = relationship("File", secondary=coursework_submission_files, overlaps="coursework_submissions")
    coursework = relationship("CourseWork", back_populates="submissions")
    student = relationship("Student", back_populates="submissions")


class ClassSchedule(Base):
    __tablename__ = 'class_schedules'
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    day_of_week = Column(Enum(DayOfWeek), nullable=False)
    start_time = Column(String, nullable=False)  
    end_time = Column(String, nullable=False)    
    room = Column(String, nullable=True)
    batch = Column(String, nullable=True)
    semester = Column(Integer, nullable=True)
    year = Column(Integer, nullable=True)
    is_active = Column(Integer, default=1)

    course = relationship("Course")


class ExamSchedule(Base):
    __tablename__ = 'exam_schedules'
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False) 
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    exam_date = Column(DateTime, nullable=False)
    start_time = Column(String, nullable=False) 
    end_time = Column(String, nullable=False)   
    room = Column(String, nullable=True)
    batch = Column(String, nullable=True)
    semester = Column(Integer, nullable=True)
    year = Column(Integer, nullable=True)

    course = relationship("Course")