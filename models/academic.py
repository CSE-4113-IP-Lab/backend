from datetime import datetime
from models import Base
from models import student_programs, faculty_programs, coursework_files, coursework_submission_files
from sqlalchemy import Column, ForeignKey, Integer, String, Enum, DateTime, Float
from sqlalchemy.orm import relationship
from models import MarkType, ProgramType, SubmissionStatus


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
    name = Column(String, unique=True, nullable=False)
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('faculties.id'), nullable=True)
    credits = Column(Integer, nullable=False)
    description = Column(String, nullable=True)

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
    submission_date = Column(String, nullable=False)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING) 

    obtained_marks = Column(Float, nullable=True)   
    feedback = Column(String, nullable=True)  

    attachments = relationship("File", secondary=coursework_submission_files, overlaps="coursework_submissions")
    coursework = relationship("CourseWork", back_populates="submissions")
    student = relationship("Student", back_populates="submissions")
