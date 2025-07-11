from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import joinedload
from typing import List
from models.administrative import PaymentTransaction
from schemas.payment import PaymentCreate, PaymentResponse, PaymentUpdate
from dependency import get_db, get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: PaymentCreate,
    db: get_db,
    current_user: get_current_user
):
    db_payment = PaymentTransaction(**payment.model_dump(), user_id=current_user.id)
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


@router.get("", response_model=List[PaymentResponse])
def get_all_payments(db: get_db):
    return db.query(PaymentTransaction).all()


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: get_db):
    payment = db.query(PaymentTransaction).filter(PaymentTransaction.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment transaction not found")
    return payment


@router.post("/my", response_model=List[PaymentResponse])
def get_my_payments(db: get_db, current_user: get_current_user):
    return (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.user_id == current_user.id)
        .all()
    )


@router.put("/{payment_id}", response_model=PaymentResponse)
def update_payment_status(
    payment_id: int,
    update_data: PaymentUpdate,
    db: get_db,
    current_user: get_current_user
):
    
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can update payment status"
        )

    payment = db.query(PaymentTransaction).filter(PaymentTransaction.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment transaction not found")

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(payment, key, value)

    db.commit()
    db.refresh(payment)
    return payment
