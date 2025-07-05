from models import Base
from models.associations import post_files
from sqlalchemy import Column, ForeignKey, Integer, String, Date, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime

from models import PostType, ScheduleType



class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(PostType), nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    date = Column(Date, nullable=False)  # Date of the post
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    attachments = relationship("File", secondary=post_files)


class Schedule(Base):
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=False)
    type = Column(Enum(ScheduleType), nullable=False)

    image_id = Column(Integer, ForeignKey('files.id'), nullable=True)

    image = relationship("File")
    program = relationship("Program", back_populates="schedules")


class AdmissionTimeline(Base):
    __tablename__ = 'admission_timelines'
    
    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=False)
    
    application_start_date = Column(String, nullable=False)
    application_end_date = Column(String, nullable=False)
    admission_exam_date = Column(String, nullable=False)
    result_publication_date = Column(String, nullable=False)
    admission_confirmation_start_date = Column(String, nullable=False)
    admission_confirmation_end_date = Column(String, nullable=False)

    attachment_id = Column(Integer, ForeignKey('files.id'), nullable=True)  
    
    attachment = relationship("File")
    program = relationship("Program", back_populates="admission_timelines")
