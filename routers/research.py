from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List, Annotated

from dependency import get_db, get_current_user
from models.administrative import ResearchContribution
from schemas.research import (
    ResearchContributionCreate,
    ResearchContributionResponse,
)
from models.user import User

router = APIRouter(prefix="/research", tags=["Researchs"])

@router.post("/", response_model=ResearchContributionResponse, status_code=status.HTTP_201_CREATED)
def create_contribution(
    contribution: ResearchContributionCreate,
    db: get_db,
    current_user: get_current_user
):
    new_contribution = ResearchContribution(**contribution.dict(), user_id=current_user.id)
    db.add(new_contribution)
    db.commit()
    db.refresh(new_contribution)
    return new_contribution

@router.get("/", response_model=List[ResearchContributionResponse])
def get_my_contributions(
    db: get_db,
    current_user: get_current_user
):
    return db.query(ResearchContribution).filter_by(user_id=current_user.id).all()


@router.put("/{contribution_id}", response_model=ResearchContributionResponse)
def update_contribution(
    contribution_id: int,
    updated_data: ResearchContributionCreate,
    db: get_db,
    current_user: get_current_user
):
    contribution = db.query(ResearchContribution).filter_by(id=contribution_id).first()
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")

    if contribution.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this contribution")

    for field, value in updated_data.dict(exclude_unset=True).items():
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
