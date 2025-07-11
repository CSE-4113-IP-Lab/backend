from fastapi import APIRouter, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, date
import os
from dotenv import load_dotenv
from dependency import get_db, get_current_user
from models.content import Post
from models.file import File as FileModel
from models.enum import UserRole
from schemas.content import PostCreate, PostUpdate, PostResponse
from utils import upload_file, delete_file

load_dotenv()

router = APIRouter(prefix="/posts", tags=["Posts"])


def is_post_archived(post_date: date) -> bool:
    """Helper function to check if a post is archived based on its date"""
    archive_days = int(os.getenv("ARCHIVE_DAYS", 30))
    archive_cutoff = datetime.now().date() - timedelta(days=archive_days)
    return post_date < archive_cutoff


def check_admin_access(current_user):
    """Helper function to check if current user has admin access"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: get_db, current_user: get_current_user):
    check_admin_access(current_user)
    db_post = Post(**post.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@router.get("", response_model=List[PostResponse])
def get_posts(db: get_db, include_archived: bool = False):
    """Get all posts. By default, only returns active posts."""
    if include_archived:
        posts = db.query(Post).all()
    else:
        archive_days = int(os.getenv("ARCHIVE_DAYS", 30))
        archive_cutoff = datetime.now().date() - timedelta(days=archive_days)
        posts = db.query(Post).filter(Post.date >= archive_cutoff).all()
    return posts


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: get_db, current_user: get_current_user):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.put("/{post_id}", response_model=PostResponse)
def update_post(post_id: int, post_update: PostUpdate, db: get_db, current_user: get_current_user):
    check_admin_access(current_user)
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    update_data = post_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)
    
    db.commit()
    db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: get_db, current_user: get_current_user):
    check_admin_access(current_user)
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    db.delete(post)
    db.commit()


@router.post("/{post_id}/attachments", response_model=PostResponse)
async def add_post_attachment(
    post_id: int, 
    db: get_db, 
    current_user: get_current_user,
    file: UploadFile = File(...)
):
    check_admin_access(current_user)
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    # Upload new file
    uploaded_file = await upload_file(db, "posts", file)
    if not uploaded_file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to upload file")
    
    # Add attachment to post
    post.attachments.append(uploaded_file)
    db.commit()
    db.refresh(post)
    
    return post


@router.delete("/{post_id}/attachments/{file_id}", response_model=PostResponse)
def remove_post_attachment(
    post_id: int, 
    file_id: int, 
    db: get_db, 
    current_user: get_current_user
):
    check_admin_access(current_user)
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    # Find the file in post attachments
    file_to_remove = None
    for attachment in post.attachments:
        if attachment.id == file_id:
            file_to_remove = attachment
            break
    
    if not file_to_remove:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    
    # Remove attachment from post
    post.attachments.remove(file_to_remove)
    
    # Delete the file
    delete_file(db, file_id)
    
    db.commit()
    db.refresh(post)
    
    return post


@router.get("/archived", response_model=List[PostResponse])
def get_archived_posts(db: get_db, current_user: get_current_user):
    """Get all archived posts (older than ARCHIVE_DAYS)"""
    archive_days = int(os.getenv("ARCHIVE_DAYS", 30))
    archive_cutoff = datetime.now().date() - timedelta(days=archive_days)
    
    archived_posts = db.query(Post).filter(Post.date < archive_cutoff).all()
    return archived_posts


@router.get("/active", response_model=List[PostResponse])
def get_active_posts(db: get_db):
    """Get all active posts (newer than ARCHIVE_DAYS)"""
    archive_days = int(os.getenv("ARCHIVE_DAYS", 30))
    archive_cutoff = datetime.now().date() - timedelta(days=archive_days)
    
    active_posts = db.query(Post).filter(Post.date >= archive_cutoff).all()
    return active_posts


@router.get("/archived/{post_id}", response_model=PostResponse)
def get_archived_post(post_id: int, db: get_db, current_user: get_current_user):
    """Get a specific archived post by ID"""
    archive_days = int(os.getenv("ARCHIVE_DAYS", 30))
    archive_cutoff = datetime.now().date() - timedelta(days=archive_days)
    
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.date < archive_cutoff
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Archived post not found"
        )
    return post


@router.get("/stats/archive")
def get_archive_stats(db: get_db, current_user: get_current_user):
    """Get archive statistics - total active and archived posts count (Admin only)"""
    check_admin_access(current_user)
    archive_days = int(os.getenv("ARCHIVE_DAYS", 30))
    archive_cutoff = datetime.now().date() - timedelta(days=archive_days)
    
    total_posts = db.query(Post).count()
    active_posts = db.query(Post).filter(Post.date >= archive_cutoff).count()
    archived_posts = db.query(Post).filter(Post.date < archive_cutoff).count()
    
    return {
        "total_posts": total_posts,
        "active_posts": active_posts,
        "archived_posts": archived_posts,
        "archive_days": archive_days,
        "archive_cutoff_date": archive_cutoff
    }
