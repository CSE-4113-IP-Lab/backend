from pydantic import BaseModel
from typing import Optional
from schemas import UserResponse

class ResearchContributionBase(BaseModel):
    type: str
    title: str
    description: Optional[str] = None
    date: str  # or `date` if using `DATE` type in DB
    institution: Optional[str] = None
    journal: Optional[str] = None
    link: Optional[str] = None  
    supervisor_id: Optional[int] = None

class ResearchContributionCreate(ResearchContributionBase):
    pass

class ResearchContributionUpdate(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    institution: Optional[str] = None
    journal: Optional[str] = None
    link: Optional[str] = None
    supervisor_id: Optional[int] = None

class ResearchContributionResponse(ResearchContributionBase):
    id: int
    user_id: int
    supervisor: Optional[UserResponse] = None
    user: UserResponse

    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2
