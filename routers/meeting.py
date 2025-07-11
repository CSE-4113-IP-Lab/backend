from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import List
from models.administrative import Meeting, MeetingParticipant
from schemas.meeting import MeetingCreate, MeetingResponse, MeetingUpdate, ParticipantCreate, ParticipantResponse
from dependency import get_db, get_current_user

router = APIRouter(prefix="/meetings", tags=["Meetings"])


# --- Create Meeting ---
@router.post("", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
def create_meeting(meeting: MeetingCreate, db: get_db, current_user: get_current_user):
    print(f"Current user {current_user.id}")
    db_meeting = Meeting(**meeting.model_dump(), created_by=current_user.id)
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting


# --- Get All Meetings ---
@router.get("", response_model=List[MeetingResponse])
def get_meetings(db: get_db):
    meetings = db.query(Meeting).all()
    return meetings


# --- Get One Meeting ---
@router.get("/{meeting_id}", response_model=MeetingResponse)
def get_meeting(meeting_id: int, db: get_db):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting


# --- Update Meeting ---
@router.put("/{meeting_id}", response_model=MeetingResponse)
def update_meeting(meeting_id: int, meeting_update: MeetingUpdate, db: get_db, current_user: get_current_user):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    if meeting.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this meeting")

    for key, value in meeting_update.dict(exclude_unset=True).items():
        setattr(meeting, key, value)
    
    db.commit()
    db.refresh(meeting)
    return meeting

@router.get("/invited/{user_id}", response_model=List[MeetingResponse])
def get_invited_meetings(user_id: int, db: get_db):
    print("User ID:", user_id)
    participants = (
        db.query(MeetingParticipant)
        .options(joinedload(MeetingParticipant.meeting))  # eager load meeting
        .filter(MeetingParticipant.user_id == user_id)
        .all()
    )

    meetings = [p.meeting for p in participants if p.meeting is not None]
    return meetings

@router.post("/my-created", response_model=List[MeetingResponse])
def get_my_created_meetings(
    db: get_db,
    current_user: get_current_user
):
    meetings = (
        db.query(Meeting)
        .filter(Meeting.created_by == current_user.id)
        .all()
    )
    return meetings


@router.post("/my-invites", response_model=List[MeetingResponse])
def get_my_invited_meetings(db: get_db, current_user: get_current_user):
    participants = (
        db.query(MeetingParticipant)
        .options(joinedload(MeetingParticipant.meeting))
        .filter(MeetingParticipant.user_id == current_user.id)
        .all()
    )
    meetings = [p.meeting for p in participants if p.meeting is not None]
    return meetings