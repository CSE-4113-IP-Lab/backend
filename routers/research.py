from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List, Annotated

from dependency import get_db, get_current_user
from models.administrative import ResearchContribution
from schemas.research import (
    ResearchContributionCreate,
    ResearchContributionUpdate,
    ResearchContributionResponse,
)
from models.user import User

router = APIRouter(prefix="/researchs", tags=["Researchs"])

@router.post("", response_model=ResearchContributionResponse, status_code=status.HTTP_201_CREATED)
def create_contribution(
    contribution: ResearchContributionCreate,
    db: get_db,
    current_user: get_current_user
):
    new_contribution = ResearchContribution(**contribution.model_dump(), user_id=current_user.id)
    db.add(new_contribution)
    db.commit()
    db.refresh(new_contribution)
    return new_contribution

@router.get("", response_model=List[ResearchContributionResponse])
def get_my_contributions(
    db: get_db,
    skip: int = 0,
    limit: int = 100,
    type: str = None,
    title: str = None,
    institution: str = None,
    journal: str = None,
    date_from: str = None,
    date_to: str = None,
    supervisor_id: int = None
):
    query = db.query(ResearchContribution)
    
    # Apply filters based on query parameters
    if type:
        query = query.filter(ResearchContribution.type.ilike(f"%{type}%"))
    
    if title:
        query = query.filter(ResearchContribution.title.ilike(f"%{title}%"))
    
    if institution:
        query = query.filter(ResearchContribution.institution.ilike(f"%{institution}%"))
    
    if journal:
        query = query.filter(ResearchContribution.journal.ilike(f"%{journal}%"))
    
    if date_from:
        query = query.filter(ResearchContribution.date >= date_from)
    
    if date_to:
        query = query.filter(ResearchContribution.date <= date_to)
    
    if supervisor_id:
        query = query.filter(ResearchContribution.supervisor_id == supervisor_id)
    
    return query.offset(skip).limit(limit).all()


@router.put("/{contribution_id}", response_model=ResearchContributionResponse)
def update_contribution(
    contribution_id: int,
    updated_data: ResearchContributionUpdate,
    db: get_db,
    current_user: get_current_user
):
    contribution = db.query(ResearchContribution).filter_by(id=contribution_id).first()
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")
    
    # Check authorization - only the owner can update their contribution
    if contribution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this contribution")

    # Use model_dump() instead of model_dump(exclude_unset=True) for updates
    update_data = updated_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(contribution, field, value)

    db.commit()
    db.refresh(contribution)
    return contribution

@router.delete("/{contribution_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contribution(
    contribution_id: int,
    db: get_db,
    current_user: get_current_user
):
    contribution = db.query(ResearchContribution).filter_by(id=contribution_id).first()
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")

    if contribution.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this contribution")

    db.delete(contribution)
    db.commit()

@router.get("/{contribution_id}", response_model=ResearchContributionResponse)
def get_contribution(
    contribution_id: int,
    db:get_db
):
    contribution = db.query(ResearchContribution).filter_by(id=contribution_id).first()
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")
    return contribution


@router.get("/user/{user_id}", response_model=List[ResearchContributionResponse])
def get_contributions_by_user(
    user_id: int,
    db: get_db
):
    return db.query(ResearchContribution).filter_by(user_id=user_id).all()
