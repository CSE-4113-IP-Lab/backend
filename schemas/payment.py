from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from models import StatusType
from schemas import ProgramResponse, UserResponse
from schemas.user import StudentResponse


class PaymentBase(BaseModel):
    program_id: Optional[int] = None
    amount: int
    payment_method: str


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    status: Optional[StatusType] = None


class PaymentResponse(PaymentBase):
    id: int
    student_id: int
    student: Optional[StudentResponse] = None
    program: Optional[ProgramResponse] = None  
    transaction_date: datetime
    status: StatusType

    class Config:
        from_attributes = True


# PaymentFee schemas
class PaymentFeeBase(BaseModel):
    program_id: int
    amount: int
    description: Optional[str] = None
    due_date: datetime


class PaymentFeeCreate(PaymentFeeBase):
    pass


class PaymentFeeUpdate(BaseModel):
    amount: Optional[int] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None


class PaymentFeeResponse(PaymentFeeBase):
    id: int
    program: Optional[ProgramResponse] = None

    class Config:
        from_attributes = True
