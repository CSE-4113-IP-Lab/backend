from models import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Enum, DateTime, Text, Time
from sqlalchemy.orm import relationship
from datetime import datetime, time
from models.enum import RoomStatus, RoomBookingStatus


class Room(Base):
    __tablename__ = 'rooms'
    
    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, unique=True, nullable=False)
    purpose = Column(String, nullable=False)  # e.g., "Classroom", "Lab", "Meeting Room", "Auditorium"
    capacity = Column(Integer, nullable=False)
    location = Column(String, nullable=True)  # Building/Floor info
    description = Column(Text, nullable=True)
    status = Column(Enum(RoomStatus), default=RoomStatus.AVAILABLE)
    
    # Room operating hours (default 8 AM to 8 PM)
    operating_start_time = Column(Time, default=time(8, 0))  # 8:00 AM
    operating_end_time = Column(Time, default=time(20, 0))   # 8:00 PM
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = relationship("RoomBooking", back_populates="room")


class RoomBooking(Base):
    __tablename__ = 'room_bookings'
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Who booked the room
    
    # Booking details
    purpose = Column(String, nullable=False)  # Purpose of booking
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    
    # Booking status
    status = Column(Enum(RoomBookingStatus), default=RoomBookingStatus.SCHEDULED)
    
    # Additional info
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Approved by admin/faculty (if approval required)
    approved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Relationships
    room = relationship("Room", back_populates="bookings")
    user = relationship("User", foreign_keys=[user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])


class TimeSlot(Base):
    """Available time slots for room booking"""
    __tablename__ = 'time_slots'
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    is_available = Column(Integer, default=1)  # 1=available, 0=booked
    
    # Relationships
    room = relationship("Room")
