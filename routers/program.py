from fastapi import APIRouter, HTTPException, status
from typing import List
from dependency import get_db, get_current_user
from models.academic import Program
from schemas.academic import ProgramCreate, ProgramUpdate, ProgramResponse

router = APIRouter(prefix="/programs", tags=["Programs"])


@router.post("", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
def create_program(program: ProgramCreate, db: get_db, current_user: get_current_user):
    db_program = Program(**program.model_dump())
    db.add(db_program)
    db.commit()
    db.refresh(db_program)
    return db_program


@router.get("", response_model=List[ProgramResponse])
def get_programs(db: get_db, current_user: get_current_user):
    programs = db.query(Program).all()
    return programs


@router.get("/{program_id}", response_model=ProgramResponse)
def get_program(program_id: int, db: get_db, current_user: get_current_user):
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    return program


@router.put("/{program_id}", response_model=ProgramResponse)
def update_program(program_id: int, program_update: ProgramUpdate, db: get_db, current_user: get_current_user):
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    
    update_data = program_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(program, field, value)
    
    db.commit()
    db.refresh(program)
    return program


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_program(program_id: int, db: get_db, current_user: get_current_user):
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    
    db.delete(program)
    db.commit()
