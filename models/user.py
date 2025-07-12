from models import Base
from models.associations import student_programs, faculty_programs
from sqlalchemy import Column, ForeignKey, Integer, String, Enum, Text
from sqlalchemy.orm import relationship
from models import UserRole


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)  
    password = Column(String, nullable=True)
    is_verified = Column(Integer, default=0)
    role = Column(Enum(UserRole), default=UserRole.USER)
    gender = Column(String, nullable=True)

    image_id = Column(Integer, ForeignKey('files.id'), nullable=True)

    image = relationship("File", uselist=False)
    student = relationship("Student", back_populates="user")
    faculty = relationship("Faculty", back_populates="user")
    created_meetings = relationship("Meeting", back_populates="creator")
    meeting_participations = relationship("MeetingParticipant", back_populates="user")
    research_contributions = relationship("ResearchContribution", back_populates="user")
    bookings = relationship("Booking", back_populates="request_by")
    posts = relationship("Post", secondary="post_participants", back_populates="participants")


class Student(Base):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    year = Column(Integer, nullable=True)
    semester = Column(Integer, nullable=True)
    registration_number = Column(String, unique=True, nullable=True)
    session = Column(String, nullable=True)

    user = relationship("User", back_populates="student")
    programs = relationship("Program", secondary=student_programs, back_populates="students")
    marks = relationship("Mark", back_populates="student")
    submissions = relationship("CourseWorkSubmission", back_populates="student")
    payment_transactions = relationship("PaymentTransaction", back_populates="student")


class Faculty(Base):
    __tablename__ = 'faculties'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    bio = Column(Text, nullable=True)
    
    designation = Column(String, nullable=True)
    joining_date = Column(String, nullable=True)

    user = relationship("User", back_populates="faculty")
    courses = relationship("Course", back_populates="teacher")
    programs = relationship("Program", secondary=faculty_programs, back_populates="faculties")
