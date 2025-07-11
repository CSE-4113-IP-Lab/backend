from pydantic import BaseModel
from typing import Optional
from schemas import UserBase

class SystemLogResponse(BaseModel):
    id: int
    action: str
    user_id: int
    user: Optional[UserBase] = None
    timestamp: str

    class Config:
        from_attributes = True