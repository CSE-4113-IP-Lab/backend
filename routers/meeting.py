from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import List, Optional
from models.administrative import Meeting, MeetingParticipant
from models.enum import MeetingStatusType, InviteStatusType
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


# --- Get All Meetings with Query Parameters ---
@router.get("", response_model=List[MeetingResponse])
def get_meetings(
    db: get_db,
    current_user: get_current_user,
    status: Optional[MeetingStatusType] = Query(None, description="Filter by meeting status"),
):
    """
    Get meetings with optional filters:
    - status: Filter by meeting status (scheduled, ongoing, completed, cancelled)
    """
    query = db.query(Meeting)
    
    # Filter by status if provided
    if status:
        query = query.filter(Meeting.status == status)
    
    
    # If neither created nor invited filters are specified, return all meetings
    # (this maintains backward compatibility)
    
    meetings = query.all()
    return meetings


# --- Update Meeting ---
@router.put("/{meeting_id}", response_model=MeetingResponse)
def update_meeting(meeting_id: int, meeting_update: MeetingUpdate, db: get_db, current_user: get_current_user):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    if meeting.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this meeting")

    for key, value in meeting_update.model_dump(exclude_unset=True).items():
        setattr(meeting, key, value)
    
    db.commit()
    db.refresh(meeting)
    return meeting

@router.get("/created/me", response_model=List[MeetingResponse])
def get_my_created_meetings(
    db: get_db,
    current_user: get_current_user,
    status: Optional[MeetingStatusType] = Query(None, description="Filter by meeting status")
):
    meetings = (
        db.query(Meeting)
        .filter(Meeting.created_by == current_user.id)
    )

    if status:
        meetings = meetings.filter(Meeting.status == status).all()

   
    return meetings


@router.get("/invites/me", response_model=List[MeetingResponse])
def get_my_invited_meetings(db: get_db, current_user: get_current_user,
                            status: Optional[MeetingStatusType] = Query(None, description="Filter by meeting status")):
    
    meetings =  db.query(Meeting).join(MeetingParticipant).filter(
        MeetingParticipant.user_id == current_user.id,
        MeetingParticipant.status == InviteStatusType.INVITED
    )

    if status:
        meetings = meetings.filter(Meeting.status == status)

    return meetings


# --- Additional Comprehensive Endpoints ---

@router.get("/my-meetings", response_model=List[MeetingResponse])
def get_my_meetings(
    db: get_db,
    current_user: get_current_user,
    status: Optional[MeetingStatusType] = Query(None, description="Filter by meeting status"),
):
    """
    Get all meetings related to the current user (created or invited)
    """
   

    base_query = db.query(Meeting)

    if status:
        base_query = base_query.filter(Meeting.status == status)

    created_meetings = base_query.filter(
        Meeting.created_by == current_user.id
    ).all()
    # Get both created and invited meetings
    accepted_meetings = (
        base_query.join(MeetingParticipant)
        .filter(
            MeetingParticipant.user_id == current_user.id,
            MeetingParticipant.status == InviteStatusType.ACCEPTED
        )
        .all()
    )

    all_meetings = created_meetings + accepted_meetings
    return all_meetings



# --- Get One Meeting ---
@router.get("/{meeting_id}", response_model=MeetingResponse)
def get_meeting(meeting_id: int, db: get_db):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting



@router.post("/{meeting_id}/participants", response_model=dict)
def add_meeting_participant(
    meeting_id: int,
    participant: ParticipantCreate,
    db: get_db,
    current_user: get_current_user
):
    """
    Add a participant to a meeting (only meeting creator can do this)
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    
    if meeting.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only meeting creator can add participants")
    
    # Check if user is already a participant
    existing_participant = db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id,
        MeetingParticipant.user_id == participant.user_id
    ).first()
    
    if existing_participant:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a participant")
    
    # Add participant
    db_participant = MeetingParticipant(
        meeting_id=meeting_id,
        user_id=participant.user_id,
        status=participant.status
    )
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)
    
    return {"message": "Participant added successfully", "participant_id": db_participant.id}

@router.put("/{meeting_id}/participants/{participant_id}/status")
def update_participant_status(
    meeting_id: int,
    participant_id: int,
    new_status: InviteStatusType,
    db: get_db,
    current_user: get_current_user
):
    """
    Update participant invitation status
    """
    participant = db.query(MeetingParticipant).filter(
        MeetingParticipant.id == participant_id,
        MeetingParticipant.meeting_id == meeting_id
    ).first()
    
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")
    
    # Only the participant themselves or meeting creator can update status
    if participant.user_id != current_user.id and participant.meeting.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    participant.status = new_status
    db.commit()
    
    return {"message": f"Participant status updated to {new_status.value}"}

@router.delete("/{meeting_id}/participants/{participant_id}")
def remove_meeting_participant(
    meeting_id: int,
    participant_id: int,
    db: get_db,
    current_user: get_current_user
):
    """
    Remove a participant from a meeting
    """
    participant = db.query(MeetingParticipant).filter(
        MeetingParticipant.id == participant_id,
        MeetingParticipant.meeting_id == meeting_id
    ).first()
    
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")
    
    # Only meeting creator or the participant themselves can remove
    if participant.meeting.created_by != current_user.id and participant.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    db.delete(participant)
    db.commit()
    
    return {"message": "Participant removed successfully"}
