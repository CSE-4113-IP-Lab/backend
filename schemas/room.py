from pydantic import BaseModel, validator
from datetime import datetime, time
from typing import Optional, List
from models.enum import RoomStatus, RoomBookingStatus


class RoomBase(BaseModel):
    room_number: str
    purpose: str
    capacity: int
    location: Optional[str] = None
    description: Optional[str] = None
    status: RoomStatus = RoomStatus.AVAILABLE
    operating_start_time: time = time(8, 0)
    operating_end_time: time = time(20, 0)


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    purpose: Optional[str] = None
    capacity: Optional[int] = None
    location: Optional[str] = None
    description: Optional[str] = None
    status: Optional[RoomStatus] = None
    operating_start_time: Optional[time] = None
    operating_end_time: Optional[time] = None


class TimeSlotInfo(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    is_available: bool


class RoomResponse(RoomBase):
    id: int
    created_at: datetime
    updated_at: datetime
    available_slots: Optional[List[TimeSlotInfo]] = []
    
    class Config:
        from_attributes = True


class RoomBookingBase(BaseModel):
    room_id: int
    purpose: str
    start_datetime: datetime
    end_datetime: datetime
    notes: Optional[str] = None
    
    @validator('end_datetime')
    def end_after_start(cls, v, values):
        if 'start_datetime' in values and v <= values['start_datetime']:
            raise ValueError('End time must be after start time')
        return v


class RoomBookingCreate(RoomBookingBase):
    pass


class RoomBookingUpdate(BaseModel):
    purpose: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[RoomBookingStatus] = None


class RoomBookingResponse(RoomBookingBase):
    id: int
    user_id: int
    status: RoomBookingStatus
    created_at: datetime
    updated_at: datetime
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    
    # Related data
    room: Optional["RoomResponse"] = None
    user_name: Optional[str] = None
    approved_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class AvailableRoomsRequest(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    purpose: Optional[str] = None
    capacity: Optional[int] = None


class BookRoomRequest(BaseModel):
    room_id: int
    start_datetime: datetime
    duration_hours: int
    duration_minutes: int
    purpose: str
    notes: Optional[str] = None
    
    @validator('duration_hours')
    def validate_duration_hours(cls, v):
        if v < 0 or v > 12:
            raise ValueError('Duration hours must be between 0 and 12')
        return v
    
    @validator('duration_minutes')
    def validate_duration_minutes(cls, v):
        if v < 0 or v >= 60:
            raise ValueError('Duration minutes must be between 0 and 59')
        return v
