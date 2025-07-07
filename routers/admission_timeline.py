from fastapi import APIRouter, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from dependency import get_db, get_current_user
from models.content import AdmissionTimeline
from schemas.content import AdmissionTimelineCreate, AdmissionTimelineUpdate, AdmissionTimelineResponse
from utils import upload_file, delete_file

router = APIRouter(prefix="/admission-timelines", tags=["Admission Timelines"])


@router.post("", response_model=AdmissionTimelineResponse, status_code=status.HTTP_201_CREATED)
def create_admission_timeline(timeline: AdmissionTimelineCreate, db: get_db, current_user: get_current_user):
    db_timeline = AdmissionTimeline(**timeline.model_dump())
    db.add(db_timeline)
    db.commit()
    db.refresh(db_timeline)
    return db_timeline              


@router.get("/all", response_model=List[AdmissionTimelineResponse])
def get_admission_timelines(db: get_db, current_user: get_current_user):
    timelines = db.query(AdmissionTimeline).all()
    return timelines


@router.get("/{timeline_id}", response_model=AdmissionTimelineResponse)
def get_admission_timeline(timeline_id: int, db: get_db, current_user: get_current_user):
    timeline = db.query(AdmissionTimeline).filter(AdmissionTimeline.id == timeline_id).first()
    if not timeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admission timeline not found")
    return timeline


@router.put("/{timeline_id}", response_model=AdmissionTimelineResponse)
def update_admission_timeline(timeline_id: int, timeline_update: AdmissionTimelineUpdate, db: get_db, current_user: get_current_user):
    timeline = db.query(AdmissionTimeline).filter(AdmissionTimeline.id == timeline_id).first()
    if not timeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admission timeline not found")
    
    update_data = timeline_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(timeline, field, value)
    
    db.commit()
    db.refresh(timeline)
    return timeline


@router.delete("/{timeline_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admission_timeline(timeline_id: int, db: get_db, current_user: get_current_user):
    timeline = db.query(AdmissionTimeline).filter(AdmissionTimeline.id == timeline_id).first()
    if not timeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admission timeline not found")
    
    db.delete(timeline)
    db.commit()


@router.put("/{timeline_id}/attachment", response_model=AdmissionTimelineResponse)
async def update_admission_timeline_attachment(
    timeline_id: int, 
    db: get_db, 
    current_user: get_current_user,
    file: UploadFile = File(...)
):
    timeline = db.query(AdmissionTimeline).filter(AdmissionTimeline.id == timeline_id).first()
    if not timeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admission timeline not found")
    
    # Delete previous attachment if exists
    if timeline.attachment_id: 
        delete_file(db, timeline.attachment_id)
    
    # Upload new file
    uploaded_file = await upload_file(db, "admission_timelines", file)
    if not uploaded_file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to upload file")
    
    # Update timeline with new attachment
    timeline.attachment_id = uploaded_file.id
    db.commit()
    db.refresh(timeline)
    
    return timeline
