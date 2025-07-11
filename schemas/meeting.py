from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time
from models.administrative import MeetingStatusType, InviteStatusType


# ---------- Participant Schemas ----------

class ParticipantBase(BaseModel):
    user_id: int
    status: Optional[InviteStatusType] = InviteStatusType.INVITED

class ParticipantCreate(ParticipantBase):
    pass

class ParticipantResponse(ParticipantBase):
    id: int
    class Config:
        orm_mode = True


# ---------- Meeting Schemas ----------

class MeetingBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: date
    time: time
    platform: Optional[str] = None
    location: str
    status: Optional[MeetingStatusType] = MeetingStatusType.SCHEDULED

class MeetingCreate(MeetingBase):
    pass

class MeetingUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    date: Optional[date]
    time: Optional[time]
    location: Optional[str]
    status: Optional[MeetingStatusType]

class MeetingResponse(MeetingBase):
    id: int
    created_by: int
    participants: List[ParticipantResponse] = []

    class Config:
        orm_mode = True
