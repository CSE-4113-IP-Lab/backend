from models import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Enum, func, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime

from models import StatusType, BookingType
from models.enum import EquipmentRequestStatus


class Equipment(Base):
    __tablename__ = 'equipments'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(String, nullable=False) 
    quantity = Column(Integer, nullable=False)
    available_quantity = Column(Integer, nullable=False)  # Track available quantity directly
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    image_id = Column(Integer, ForeignKey('files.id'), nullable=True)
    image = relationship("File")
    
    equipment_requests = relationship("EquipmentRequest", back_populates="equipment")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'available_quantity' not in kwargs:
            self.available_quantity = self.quantity


class EquipmentRequest(Base):
    __tablename__ = 'equipment_requests'
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey('equipments.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(Enum(EquipmentRequestStatus), default=EquipmentRequestStatus.PENDING)
    purpose = Column(Text, nullable=True)
    request_date = Column(DateTime, default=datetime.utcnow)
    approved_date = Column(DateTime, nullable=True)
    handover_date = Column(DateTime, nullable=True)
    return_date = Column(DateTime, nullable=True)
    approved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    notes = Column(Text, nullable=True)
    
    equipment = relationship("Equipment", back_populates="equipment_requests")
    user = relationship("User", foreign_keys=[user_id], back_populates="equipment_requests")
    approved_by = relationship("User", foreign_keys=[approved_by_id])


class EquipmentEntry(Base):
    __tablename__ = 'equipment_entries'
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey('equipments.id'), nullable=False)
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=False)
    quantity = Column(Integer, nullable=False)

    
    equipment = relationship("Equipment")
    booking = relationship("Booking", back_populates="equipment_entries")

class Booking(Base):
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(BookingType), nullable=False)  
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    date = Column(String, nullable=False)
    status = Column(Enum(StatusType), default=StatusType.PENDING)
    request_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    request_by = relationship("User", back_populates="bookings")
    equipment_entries = relationship("EquipmentEntry", back_populates="booking")
