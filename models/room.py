from models import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Enum, DateTime, Text, Time, Date, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, time, date
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
    
    # Room operating hours (8 AM to 8 PM by default)
    operating_start_time = Column(Time, default=time(8, 0))  # 8:00 AM
    operating_end_time = Column(Time, default=time(20, 0))   # 8:00 PM
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = relationship("RoomBooking", back_populates="room")
    time_slots = relationship("RoomTimeSlot", back_populates="room", cascade="all, delete-orphan")


class RoomTimeSlot(Base):
    """30-minute time slots for each room for 7 days (0-6, where 0 is today)"""
    __tablename__ = 'room_time_slots'
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    day_offset = Column(Integer, nullable=False)  # 0-6 (0=today, 1=tomorrow, etc.)
    slot_date = Column(Date, nullable=False)  # Actual date for this slot
    slot_time = Column(Time, nullable=False)  # Start time of 30-min slot (e.g., 08:00, 08:30, 09:00)
    is_available = Column(Boolean, default=True)  # True=available, False=booked
    
    # Booking reference if slot is booked
    booking_id = Column(Integer, ForeignKey('room_bookings.id'), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    room = relationship("Room", back_populates="time_slots")
    booking = relationship("RoomBooking", back_populates="time_slots")


class RoomBooking(Base):
    __tablename__ = 'room_bookings'
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Who booked the room
    
    # Booking details
    purpose = Column(String, nullable=False)  # Purpose of booking
    booking_date = Column(Date, nullable=False)  # Date of booking
    start_time = Column(Time, nullable=False)  # Start time (e.g., 09:00)
    end_time = Column(Time, nullable=False)    # End time (e.g., 10:30)
    duration_slots = Column(Integer, nullable=False)  # Number of 30-min slots
    
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
    time_slots = relationship("RoomTimeSlot", back_populates="booking")


# Keep the original TimeSlot for backward compatibility
class TimeSlot(Base):
    """Legacy time slots - kept for backward compatibility"""
    __tablename__ = 'time_slots'
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    is_available = Column(Integer, default=1)  # 1=available, 0=booked
    
    # Relationships
    room = relationship("Room")
