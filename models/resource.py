from models import Base
from sqlalchemy import Column, ForeignKey, Integer, String, Enum, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from models.enum import StatusType


class Equipment(Base):
    __tablename__ = 'equipments'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(String, nullable=False) 
    quantity = Column(Integer, nullable=False)
    description = Column(String, nullable=True)

    image_id = Column(Integer, ForeignKey('files.id'), nullable=True)
    image = relationship("File")
    
    entries = relationship("EquipmentEntry", back_populates="equipment")

    @hybrid_property
    def available_quantity(self):
        """Calculate available quantity based on total quantity minus entries"""
        if self.entries:
            used_quantity = sum(entry.quantity for entry in self.entries)
            return self.quantity - used_quantity
        return self.quantity

    @available_quantity.expression
    def available_quantity(cls):
        """SQL expression for available_quantity for database queries"""
        return cls.quantity - func.coalesce(
            func.sum(EquipmentEntry.quantity), 0
        )


class EquipmentEntry(Base):
    __tablename__ = 'equipment_entries'
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey('equipments.id'), nullable=False)
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=False)
    quantity = Column(Integer, nullable=False)

    
    equipment = relationship("Equipment", back_populates="entries")
    booking = relationship("Booking", back_populates="equipment_entries")

class Booking(Base):
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    date = Column(String, nullable=False)
    status = Column(Enum(StatusType), default=StatusType.PENDING)

    equipment_entries = relationship("EquipmentEntry", back_populates="booking")
