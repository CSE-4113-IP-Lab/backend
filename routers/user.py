from fastapi import APIRouter, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from dependency import get_db, get_current_user
from models.user import User
from models.file import File as FileModel
from schemas.user import  UserUpdate, UserResponse, PasswordChangeRequest
from utils import upload_file, delete_file, hash, verify



router = APIRouter(prefix="/users", tags=["Users"])



@router.get("", response_model=List[UserResponse])
def get_users(current_user: get_current_user, db: get_db, skip: int = 0, limit: int = 100, role: str = None):
    query = db.query(User).offset(skip).limit(limit)
    if role:
        query = query.filter(User.role == role)
    users = query.all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: get_db, current_user: get_current_user):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: get_db, current_user: get_current_user):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Check for unique constraints if updating
    if 'email' in update_data:
        existing_user = db.query(User).filter(User.email == update_data['email'], User.id != user_id).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    
    if 'username' in update_data:
        existing_user = db.query(User).filter(User.username == update_data['username'], User.id != user_id).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    
    if 'phone' in update_data and update_data['phone'] is not None:
        existing_user = db.query(User).filter(User.phone == update_data['phone'], User.id != user_id).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone number already registered")
    
    # Update user fields
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: get_db, current_user: get_current_user):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Delete user's image if exists
    if user.image_id:
        delete_file(db, user.image_id)
    
    db.delete(user)
    db.commit()


@router.put("/{user_id}/image", response_model=UserResponse)
async def upload_user_image(
    user_id: int, 
    db: get_db, 
    current_user: get_current_user,
    file: UploadFile = File(...)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Delete previous image if exists
    if user.image_id:
        delete_file(db, user.image_id)
    
    # Upload new image
    uploaded_file = await upload_file(db, "users", file)
    if not uploaded_file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to upload image")
    
    # Update user with new image
    user.image_id = uploaded_file.id
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/{user_id}/image", response_model=UserResponse)
def delete_user_image(
    user_id: int, 
    db: get_db, 
    current_user: get_current_user
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if not user.image_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User has no image")
    
    # Delete the image file
    delete_file(db, user.image_id)
    
    # Remove image reference from user
    user.image_id = None
    db.commit()
    db.refresh(user)
    
    return user


@router.get("/me/profile", response_model=UserResponse)
def get_current_user_profile(current_user: get_current_user):
    return current_user


@router.put("/{user_id}/password", response_model=dict)
def change_user_password(
    user_id: int, 
    password_request: PasswordChangeRequest, 
    db: get_db, 
    current_user: get_current_user
):
    # Find the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Check if passwords match
    if password_request.new_password != password_request.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New passwords do not match")
    
    # Verify current password
    if not verify(password_request.current_password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    
    # Hash and update new password
    user.password = hash(password_request.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.put("/me/password", response_model=dict)
def change_current_user_password(
    password_request: PasswordChangeRequest, 
    db: get_db, 
    current_user: get_current_user
):
    return change_user_password(current_user.id, password_request, db, current_user)

