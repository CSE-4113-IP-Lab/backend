from datetime import datetime
from models import Base
from sqlalchemy import Column, Integer, String, Date, Time, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from models.enum import MeetingStatusType, StatusType


class Meeting(Base):
    __tablename__ = 'meetings'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False) 
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    location = Column(String, nullable=False) 
    
    creator = relationship("User", back_populates="created_meetings")
    participants = relationship("MeetingParticipant", back_populates="meeting")



class MeetingParticipant(Base):
    __tablename__ = 'meeting_participants'
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(Enum(MeetingStatusType), default=MeetingStatusType.INVITED)

    meeting = relationship("Meeting", back_populates="participants")
    user = relationship("User", back_populates="meeting_participations")


class PaymentTransaction(Base):
    __tablename__ = 'payment_transactions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=True)  
    amount = Column(Integer, nullable=False)
    transaction_date = Column(DateTime, nullable=False, default=datetime.now)
    status = Column(Enum(StatusType), default=StatusType.PENDING)
    payment_method = Column(String, nullable=False)

    user = relationship("User", back_populates="payment_transactions")
    course = relationship("Course", back_populates="transactions")


class ResearchContribution(Base):
    __tablename__ = 'research_contributions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(String, nullable=False)  
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    date = Column(String, nullable=False)  
    institution = Column(String, nullable=True)  
    journal = Column(String, nullable=True)
    link = Column(String, nullable=True)  
    
    user = relationship("User", back_populates="research_contributions")
