from typing import List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models.enum import BookingType, StatusType, EquipmentRequestStatus
from models.resource import Equipment, Booking, EquipmentEntry, EquipmentRequest
from datetime import datetime


# Equipment Schemas
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
    available_quantity: Optional[int] = None
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
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Equipment Request Schemas
class EquipmentRequestCreate(BaseModel):
    equipment_id: int
    quantity: int
    purpose: Optional[str] = None

class EquipmentRequestUpdate(BaseModel):
    status: Optional[EquipmentRequestStatus] = None
    notes: Optional[str] = None

class EquipmentRequestResponse(BaseModel):
    id: int
    equipment_id: int
    user_id: int
    quantity: int
    status: EquipmentRequestStatus
    purpose: Optional[str] = None
    request_date: datetime
    approved_date: Optional[datetime] = None
    handover_date: Optional[datetime] = None
    return_date: Optional[datetime] = None
    approved_by_id: Optional[int] = None
    notes: Optional[str] = None
    equipment: EquipmentResponse
    
    class Config:
        from_attributes = True


# Booking Schemas (keeping existing ones)
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