from pydantic import BaseModel
from typing import Optional, List
from datetime import date as Date, datetime as DateTime
from models import PostType, ScheduleType
from schemas import *


class PostBase(BaseModel):
    type: PostType
    title: str
    content: str
    date: Date


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    type: Optional[PostType] = None
    title: Optional[str] = None
    content: Optional[str] = None
    date: Optional[Date] = None


class PostResponse(PostBase):
    id: int
    created_at: DateTime
    updated_at: DateTime
    attachments: List[FileBase] = []

    class Config:
        from_attributes = True


# Schedule schemas
class ScheduleBase(BaseModel):
    program_id: int
    type: ScheduleType


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    program_id: Optional[int] = None
    type: Optional[ScheduleType] = None


class ScheduleResponse(ScheduleBase):
    id: int
    image_id: Optional[int] = None
    image: Optional[FileBase] = None

    class Config:
        from_attributes = True


# AdmissionTimeline schemas
class AdmissionTimelineBase(BaseModel):
    program_id: int
    application_start_date: str
    application_end_date: str
    admission_exam_date: str
    result_publication_date: str
    admission_confirmation_start_date: str
    admission_confirmation_end_date: str


class AdmissionTimelineCreate(AdmissionTimelineBase):
    pass


class AdmissionTimelineUpdate(BaseModel):
    program_id: Optional[int] = None
    application_start_date: Optional[str] = None
    application_end_date: Optional[str] = None
    admission_exam_date: Optional[str] = None
    result_publication_date: Optional[str] = None
    admission_confirmation_start_date: Optional[str] = None
    admission_confirmation_end_date: Optional[str] = None


class AdmissionTimelineResponse(AdmissionTimelineBase):
    id: int
    attachment_id: Optional[int] = None
    attachment: Optional[FileBase] = None

    class Config:
        from_attributes = True
