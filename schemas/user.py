from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from models import UserRole, OTPType
from schemas import FileBase

class UserLogin(BaseModel):
    email : EmailStr
    password: str

# Password change schema
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

class OAuthUserCreate(BaseModel):
    username: str
    email : EmailStr
    role : UserRole = UserRole.USER  


# OTP schemas
class OTPCreate(BaseModel):
    userEmail: EmailStr
    otp: str
    type: OTPType


class OTPVerify(BaseModel):
    userEmail: EmailStr
    otp: str
    type: OTPType


class OTPResponse(BaseModel):
    id: int
    userEmail: str
    type: OTPType
    created_at: datetime

    class Config:
        from_attributes = True


# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    phone: Optional[str] = None
    gender: Optional[str] = None
    role: Optional[UserRole] = UserRole.USER


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    gender: Optional[str] = None
    role: Optional[UserRole] = UserRole.USER


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    gender: Optional[str] = None
    role: Optional[UserRole] = None


class UserResponse(UserBase):
    id: int
    is_verified: int
    image_id: Optional[int] = None
    image: Optional[FileBase] = None

    class Config:
        from_attributes = True


# Student schemas
class StudentBase(BaseModel):
    year: Optional[int] = None
    semester: Optional[int] = None
    registration_number: Optional[str] = None
    session: Optional[str] = None


class StudentCreate(StudentBase):
    user_id: int


class StudentUpdate(BaseModel):
    # Student-specific fields
    year: Optional[int] = None
    semester: Optional[int] = None
    registration_number: Optional[str] = None
    session: Optional[str] = None
    
    # User fields that can be updated
    username: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None


class StudentResponse(StudentBase):
    id: int
    user_id: int
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


# Faculty schemas
class FacultyBase(BaseModel):
    bio: Optional[str] = None
    on_leave: Optional[int] = None 
    designation: Optional[str] = None
    joining_date: Optional[str] = None
    on_leave: Optional[int] = 0
    expertise: Optional[List[str]] = None  


class FacultyCreate(FacultyBase):
    user_id: int


class FacultyUpdate(BaseModel):
    # Faculty-specific fields
    bio: Optional[str] = None
    designation: Optional[str] = None
    joining_date: Optional[str] = None
    expertise: Optional[List[str]] = None
    # User fields that can be updated
    username: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    on_leave: Optional[int] = None


class FacultyResponse(FacultyBase):
    id: int
    user_id: int
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


# Combined user profile response
class UserProfileResponse(BaseModel):
    user: UserResponse
    student: Optional[StudentResponse] = None
    faculty: Optional[FacultyResponse] = None

    class Config:
        from_attributes = True
