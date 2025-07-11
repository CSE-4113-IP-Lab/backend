from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from dependency import get_db, get_current_user
from models.log import SystemLog
from schemas.log import SystemLogResponse

router = APIRouter(prefix="/logs", tags=["System Logs"])


@router.get("", response_model=List[SystemLogResponse])
def get_system_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start_date: Optional[date] = Query(None, description="Filter logs from this date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter logs until this date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get system logs with optional filtering.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (1-1000)
    - **action**: Filter by specific action type
    - **user_id**: Filter by specific user ID
    - **start_date**: Filter logs from this date onwards
    - **end_date**: Filter logs until this date
    """
    query = db.query(SystemLog).order_by(SystemLog.timestamp.desc())
    
    # Apply filters
    if action:
        query = query.filter(SystemLog.action.ilike(f"%{action}%"))
    
    if user_id:
        query = query.filter(SystemLog.user_id == user_id)
    
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(SystemLog.timestamp >= start_datetime)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(SystemLog.timestamp <= end_datetime)
    
    # Apply pagination
    logs = query.offset(skip).limit(limit).all()
    
    return logs


@router.get("/{log_id}", response_model=SystemLogResponse)
def get_system_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific system log by ID."""
    log = db.query(SystemLog).filter(SystemLog.id == log_id).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="System log not found"
        )
    return log


@router.get("/user/{user_id}", response_model=List[SystemLogResponse])
def get_user_logs(
    user_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    start_date: Optional[date] = Query(None, description="Filter logs from this date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter logs until this date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all logs for a specific user."""
    query = db.query(SystemLog).filter(SystemLog.user_id == user_id).order_by(SystemLog.timestamp.desc())
    
    # Apply additional filters
    if action:
        query = query.filter(SystemLog.action.ilike(f"%{action}%"))
    
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(SystemLog.timestamp >= start_datetime)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(SystemLog.timestamp <= end_datetime)
    
    logs = query.offset(skip).limit(limit).all()
    return logs


