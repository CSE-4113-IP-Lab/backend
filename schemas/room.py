from pydantic import BaseModel, validator
from datetime import datetime, time, date
from typing import Optional, List, Dict
from models.enum import RoomStatus, RoomBookingStatus


class RoomBase(BaseModel):
    room_number: Optional[str] = None
    purpose: Optional[str] = None
    capacity: Optional[int] = None
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


class RoomTimeSlotInfo(BaseModel):
    day_offset: int  # 0-6
    slot_date: date
    slot_time: time
    is_available: bool
    booking_id: Optional[int] = None


class DaySchedule(BaseModel):
    day_offset: int
    date: date
    slots: List[RoomTimeSlotInfo]


class WeeklySchedule(BaseModel):
    room_id: int
    room_number: str
    week_schedule: List[DaySchedule]


class RoomResponse(RoomBase):
    id: int
    created_at: datetime
    updated_at: datetime
    available_slots: Optional[List[TimeSlotInfo]] = []  # Backward compatibility
    weekly_schedule: Optional[WeeklySchedule] = None
    
    class Config:
        from_attributes = True


class RoomBookingBase(BaseModel):
    room_id: int
    purpose: str
    booking_date: date
    start_time: time
    end_time: time
    notes: Optional[str] = None
    
    @validator('end_time')
    def end_after_start(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    @validator('start_time', 'end_time')
    def validate_30_minute_slots(cls, v):
        """Ensure times align with 30-minute slots"""
        if v.minute not in [0, 30] or v.second != 0 or v.microsecond != 0:
            raise ValueError('Times must align with 30-minute slots (e.g., 08:00, 08:30, 09:00)')
        return v
    
    @validator('booking_date')
    def validate_booking_date(cls, v):
        """Ensure booking is within next 7 days"""
        from datetime import date, timedelta
        today = date.today()
        max_date = today + timedelta(days=6)
        if v < today or v > max_date:
            raise ValueError('Booking date must be within the next 7 days (today to day 6)')
        return v


class RoomBookingCreate(RoomBookingBase):
    pass


class RoomBookingUpdate(BaseModel):
    purpose: Optional[str] = None
    booking_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    notes: Optional[str] = None
    status: Optional[RoomBookingStatus] = None


class RoomBookingResponse(RoomBookingBase):
    id: int
    user_id: int
    duration_slots: int
    status: RoomBookingStatus
    created_at: datetime
    updated_at: datetime
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    
    # Related data
    room: Optional[Dict] = None
    user_name: Optional[str] = None
    approved_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class AvailableRoomsRequest(BaseModel):
    booking_date: date
    start_time: time
    end_time: time
    purpose: Optional[str] = None
    capacity: Optional[int] = None


class BookRoomRequest(BaseModel):
    room_id: int
    booking_date: date
    start_time: time
    end_time: time
    purpose: str
    notes: Optional[str] = None
    
    @validator('end_time')
    def end_after_start(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    @validator('start_time', 'end_time')
    def validate_30_minute_slots(cls, v):
        """Ensure times align with 30-minute slots"""
        if v.minute not in [0, 30] or v.second != 0 or v.microsecond != 0:
            raise ValueError('Times must align with 30-minute slots (e.g., 08:00, 08:30, 09:00)')
        return v
    
    @validator('booking_date')
    def validate_booking_date(cls, v):
        """Ensure booking is within next 7 days"""
        from datetime import date, timedelta
        today = date.today()
        max_date = today + timedelta(days=6)
        if v < today or v > max_date:
            raise ValueError('Booking date must be within the next 7 days (today to day 6)')
        return v


class SlotAvailabilityRequest(BaseModel):
    room_id: int
    day_offset: int  # 0-6
    
    @validator('day_offset')
    def validate_day_offset(cls, v):
        if v < 0 or v > 6:
            raise ValueError('Day offset must be between 0 and 6')
        return v
