from fastapi import APIRouter, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from dependency import get_db, get_current_user
from models.academic import CourseWork
from models.file import File as FileModel
from schemas.academic import CourseWorkCreate, CourseWorkUpdate, CourseWorkResponse
from utils import upload_file, delete_file

router = APIRouter(prefix="/courseworks", tags=["CourseWorks"])


@router.post("", response_model=CourseWorkResponse, status_code=status.HTTP_201_CREATED)
def create_coursework(coursework: CourseWorkCreate, db: get_db, current_user: get_current_user):
    db_coursework = CourseWork(**coursework.model_dump())
    db.add(db_coursework)
    db.commit()
    db.refresh(db_coursework)
    return db_coursework


@router.get("", response_model=List[CourseWorkResponse])
def get_courseworks(db: get_db, current_user: get_current_user):
    courseworks = db.query(CourseWork).all()
    return courseworks


@router.get("/{coursework_id}", response_model=CourseWorkResponse)
def get_coursework(coursework_id: int, db: get_db, current_user: get_current_user):
    coursework = db.query(CourseWork).filter(CourseWork.id == coursework_id).first()
    if not coursework:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CourseWork not found")
    return coursework


@router.put("/{coursework_id}", response_model=CourseWorkResponse)
def update_coursework(coursework_id: int, coursework_update: CourseWorkUpdate, db: get_db, current_user: get_current_user):
    coursework = db.query(CourseWork).filter(CourseWork.id == coursework_id).first()
    if not coursework:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CourseWork not found")
    
    update_data = coursework_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(coursework, field, value)
    
    db.commit()
    db.refresh(coursework)
    return coursework


@router.delete("/{coursework_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coursework(coursework_id: int, db: get_db, current_user: get_current_user):
    coursework = db.query(CourseWork).filter(CourseWork.id == coursework_id).first()
    if not coursework:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CourseWork not found")
    
    db.delete(coursework)
    db.commit()


@router.post("/{coursework_id}/attachments", response_model=CourseWorkResponse)
async def add_coursework_attachment(
    coursework_id: int, 
    db: get_db, 
    current_user: get_current_user,
    file: UploadFile = File(...)
):
    coursework = db.query(CourseWork).filter(CourseWork.id == coursework_id).first()
    if not coursework:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CourseWork not found")
    
    # Upload new file
    uploaded_file = await upload_file(db, "courseworks", file)
    if not uploaded_file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to upload file")
    
    # Add attachment to coursework
    coursework.attachments.append(uploaded_file)
    db.commit()
    db.refresh(coursework)
    
    return coursework


@router.delete("/{coursework_id}/attachments/{file_id}", response_model=CourseWorkResponse)
def remove_coursework_attachment(
    coursework_id: int, 
    file_id: int, 
    db: get_db, 
    current_user: get_current_user
):
    coursework = db.query(CourseWork).filter(CourseWork.id == coursework_id).first()
    if not coursework:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CourseWork not found")
    
    # Find the file in coursework attachments
    file_to_remove = None
    for attachment in coursework.attachments:
        if attachment.id == file_id:
            file_to_remove = attachment
            break
    
    if not file_to_remove:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    
    # Remove attachment from coursework
    coursework.attachments.remove(file_to_remove)
    
    # Delete the file
    delete_file(db, file_id)
    
    db.commit()
    db.refresh(coursework)
    
    return coursework
