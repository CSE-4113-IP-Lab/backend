import datetime
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, date
import os
from dotenv import load_dotenv
from dependency import get_db, get_current_user
from models.content import Post
from models import User
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

@router.get("/upcoming/events", response_model=List[PostResponse])
def get_upcoming_events(db: get_db, current_user: get_current_user):
    """Get all upcoming events"""
    # Assuming 'Post' has a 'date' field to filter upcoming events
    upcoming_events = db.query(Post).filter(Post.date > datetime.now()).all()
    return upcoming_events


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

@router.post("/{post_id}/participants/{user_id}")
def add_participant_to_post(
    post_id: int, 
    user_id: int, 
    db: get_db, 
    current_user: get_current_user
):
    """Add a participant to a post"""
    # Check if post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Check if user is already a participant
    if user in post.participants:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="User is already a participant in this post"
        )
    
    # Add user as participant
    post.participants.append(user)
    db.commit()
    
    return {"message": f"User {user.username} successfully added as participant to post '{post.title}'"}


@router.delete("/{post_id}/participants/{user_id}")
def remove_participant_from_post(
    post_id: int, 
    user_id: int, 
    db: get_db, 
    current_user: get_current_user
):
    """Remove a participant from a post"""
    # Check if post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Check if user is a participant
    if user not in post.participants:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User is not a participant in this post"
        )
    
    # Remove user from participants
    post.participants.remove(user)
    db.commit()
    
    return {"message": f"User {user.username} successfully removed from post '{post.title}'"}


@router.get("/{post_id}/participants")
def get_post_participants(
    post_id: int, 
    db: get_db, 
    current_user: get_current_user
):
    """Get all participants of a post"""
    # Check if post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    # Return participant information
    participants = []
    for user in post.participants:
        participants.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value if user.role else None
        })
    
    return {
        "post_id": post_id,
        "post_title": post.title,
        "participants_count": len(participants),
        "participants": participants

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
