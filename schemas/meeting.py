from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time
from models import MeetingStatusType, InviteStatusType
from schemas.user import UserResponse

class ParticipantBase(BaseModel):
    user_id: int
    status: Optional[InviteStatusType] = InviteStatusType.INVITED

class ParticipantCreate(ParticipantBase):
    pass

class ParticipantResponse(ParticipantBase):
    id: int
    user: Optional[UserResponse] = None  
    class Config:
        orm_mode = True

class MeetingBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: date
    time: time
    platform: Optional[str] = None
    link: str
    status: Optional[MeetingStatusType] = MeetingStatusType.SCHEDULED

class MeetingCreate(MeetingBase):
    pass

class MeetingUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    date: Optional[date]
    time: Optional[time]
    platform: Optional[str]
    link: Optional[str]
    status: Optional[MeetingStatusType]= MeetingStatusType.SCHEDULED

class MeetingResponse(MeetingBase):
    id: int
    created_by: int
    participants: List[ParticipantResponse] = []

    class Config:
        orm_mode = True
