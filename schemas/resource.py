from typing import List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models.enum import BookingType, StatusType
from models.resource import Equipment, Booking, EquipmentEntry


# Pydantic Models
class EquipmentCreate(BaseModel):
    name: str
    type: str
    quantity: int
    description: Optional[str] = None
    image_id: Optional[int] = None

class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    quantity: Optional[int] = None
    description: Optional[str] = None
    image_id: Optional[int] = None

class EquipmentResponse(BaseModel):
    id: int
    name: str
    type: str
    quantity: int
    available_quantity: int
    description: Optional[str] = None
    image_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class BookingCreate(BaseModel):
    type: BookingType
    start_time: str
    end_time: str
    date: str
    equipment_entries: List[dict]


class BookingUpdate(BaseModel):
    type: Optional[BookingType] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    date: Optional[str] = None
    status: Optional[StatusType] = None

class BookingResponse(BaseModel):
    id: int
    type: BookingType
    start_time: str
    end_time: str
    date: str
    status: StatusType
    request_by_id: int
    equipment_entries: List[dict]
    
    class Config:
        from_attributes = True