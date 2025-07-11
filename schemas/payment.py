from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from models.administrative import StatusType


class PaymentBase(BaseModel):
    course_id: Optional[int] = None
    amount: int
    payment_method: str


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    status: Optional[StatusType] = None


class PaymentResponse(PaymentBase):
    id: int
    user_id: int
    transaction_date: datetime
    status: StatusType

    class Config:
        orm_mode = True
