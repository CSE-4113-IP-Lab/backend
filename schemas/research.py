from pydantic import BaseModel
from typing import Optional

class ResearchContributionBase(BaseModel):
    type: str
    title: str
    description: Optional[str] = None
    date: str  # or `date` if using `DATE` type in DB
    institution: Optional[str] = None
    journal: Optional[str] = None
    link: Optional[str] = None  # changed from HttpUrl to str

class ResearchContributionCreate(ResearchContributionBase):
    pass

class ResearchContributionUpdate(ResearchContributionBase):
    pass

class ResearchContributionResponse(ResearchContributionBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True  # For SQLAlchemy model compatibility
