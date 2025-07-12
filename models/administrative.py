from datetime import datetime
from models import Base
from sqlalchemy import Column, Integer, String, Date, Time, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from models import MeetingStatusType, StatusType,InviteStatusType


class Meeting(Base):
    __tablename__ = 'meetings'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False) 
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    platform = Column(String, nullable=True)
    location = Column(String, nullable=False)
    status = Column(Enum(MeetingStatusType), default=MeetingStatusType.SCHEDULED)

    creator = relationship("User", back_populates="created_meetings")
    participants = relationship("MeetingParticipant", back_populates="meeting")



class MeetingParticipant(Base):
    __tablename__ = 'meeting_participants'
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(Enum(InviteStatusType), default=InviteStatusType.INVITED)

    meeting = relationship("Meeting", back_populates="participants")
    user = relationship("User", back_populates="meeting_participations")

class PaymentFee(Base):
    __tablename__ = 'payment_fees'
    
    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=False)
    amount = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    due_date = Column(DateTime, nullable=False)

    program = relationship("Program", back_populates="payment_fees")  

class PaymentTransaction(Base):
    __tablename__ = 'payment_transactions'
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=True)
    amount = Column(Integer, nullable=False)
    transaction_date = Column(DateTime, nullable=False, default=datetime.now)
    status = Column(Enum(StatusType), default=StatusType.PENDING)
    payment_method = Column(String, nullable=False)

    student = relationship("Student", back_populates="payment_transactions")
    program = relationship("Program", back_populates="transactions") 


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
