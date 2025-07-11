from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from models import UserRole
from schemas import FileBase

class UserLogin(BaseModel):
    email : EmailStr
    password: str

# Password change schema
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


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
    is_verified: Optional[int] = None


class UserResponse(UserBase):
    id: int
    is_verified: int
    image_id: Optional[int] = None
    image: Optional[FileBase] = None

    class Config:
        from_attributes = True


# Student schemas
class StudentBase(BaseModel):
    year: int
    semester: int
    registration_number: str
    session: str


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
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    gender: Optional[str] = None
    role: Optional[UserRole] = None
    is_verified: Optional[int] = None


class StudentResponse(StudentBase):
    id: int
    user_id: int
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


# Faculty schemas
class FacultyBase(BaseModel):
    designation: str
    joining_date: str


class FacultyCreate(FacultyBase):
    user_id: int


class FacultyUpdate(BaseModel):
    # Faculty-specific fields
    designation: Optional[str] = None
    joining_date: Optional[str] = None
    
    # User fields that can be updated
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    gender: Optional[str] = None
    role: Optional[UserRole] = None
    is_verified: Optional[int] = None


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
