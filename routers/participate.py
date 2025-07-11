from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from models.administrative import MeetingParticipant, Meeting
from schemas.meeting import ParticipantCreate, ParticipantResponse
from dependency import get_db, get_current_user

router = APIRouter(prefix="/participants", tags=["Participants"])


@router.post("/{meeting_id}", response_model=ParticipantResponse)
def add_participant(meeting_id: int, participant: ParticipantCreate, db: get_db, current_user: get_current_user):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    if meeting.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only creator can add participants")

    new_participant = MeetingParticipant(
        meeting_id=meeting_id,
        user_id=participant.user_id,
        status=participant.status,
    )
    db.add(new_participant)
    db.commit()
    db.refresh(new_participant)
    return new_participant


@router.get("/{meeting_id}", response_model=List[ParticipantResponse])
def get_participants(meeting_id: int, db: get_db):
    participants = db.query(MeetingParticipant).filter(MeetingParticipant.meeting_id == meeting_id).all()
    return participants


