from fastapi import APIRouter, HTTPException, status, UploadFile, File
from typing import List
from dependency import get_db, get_current_user
from models.academic import CourseWorkSubmission
from schemas.academic import CourseWorkSubmissionCreate, CourseWorkSubmissionUpdate, CourseWorkSubmissionResponse
from utils import upload_file, delete_file

router = APIRouter(prefix="/coursework-submissions", tags=["CourseWork Submissions"])


@router.post("", response_model=CourseWorkSubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_coursework_submission(submission: CourseWorkSubmissionCreate, db: get_db, current_user: get_current_user):
    db_submission = CourseWorkSubmission(**submission.model_dump())
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission


@router.get("", response_model=List[CourseWorkSubmissionResponse])
def get_coursework_submissions(db: get_db, current_user: get_current_user):
    submissions = db.query(CourseWorkSubmission).all()
    return submissions


@router.get("/{submission_id}", response_model=CourseWorkSubmissionResponse)
def get_coursework_submission(submission_id: int, db: get_db, current_user: get_current_user):
    submission = db.query(CourseWorkSubmission).filter(CourseWorkSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CourseWork submission not found")
    return submission


@router.put("/{submission_id}", response_model=CourseWorkSubmissionResponse)
def update_coursework_submission(submission_id: int, submission_update: CourseWorkSubmissionUpdate, db: get_db, current_user: get_current_user):
    submission = db.query(CourseWorkSubmission).filter(CourseWorkSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CourseWork submission not found")
    
    update_data = submission_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(submission, field, value)
    
    db.commit()
    db.refresh(submission)
    return submission


@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coursework_submission(submission_id: int, db: get_db, current_user: get_current_user):
    submission = db.query(CourseWorkSubmission).filter(CourseWorkSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CourseWork submission not found")
    
    db.delete(submission)
    db.commit()


@router.post("/{submission_id}/attachments", response_model=CourseWorkSubmissionResponse)
async def add_submission_attachment(
    submission_id: int, 
    db: get_db, 
    current_user: get_current_user,
    file: UploadFile = File(...)
):
    submission = db.query(CourseWorkSubmission).filter(CourseWorkSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CourseWork submission not found")
    
    # Upload new file
    uploaded_file = await upload_file(db, "coursework_submissions", file)
    if not uploaded_file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to upload file")
    
    # Add attachment to submission
    submission.attachments.append(uploaded_file)
    db.commit()
    db.refresh(submission)
    
    return submission


@router.delete("/{submission_id}/attachments/{file_id}", response_model=CourseWorkSubmissionResponse)
def remove_submission_attachment(
    submission_id: int, 
    file_id: int, 
    db: get_db, 
    current_user: get_current_user
):
    submission = db.query(CourseWorkSubmission).filter(CourseWorkSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CourseWork submission not found")
    
    # Find the file in submission attachments
    file_to_remove = None
    for attachment in submission.attachments:
        if attachment.id == file_id:
            file_to_remove = attachment
            break
    
    if not file_to_remove:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    
    # Remove attachment from submission
    submission.attachments.remove(file_to_remove)
    
    # Delete the file
    delete_file(db, file_id)
    
    db.commit()
    db.refresh(submission)
    
    return submission
