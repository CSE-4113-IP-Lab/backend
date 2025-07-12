from fastapi import APIRouter, HTTPException, status
from typing import List
from models import Student, PaymentTransaction, PaymentFee, UserRole, StatusType
from schemas import (
    PaymentCreate, PaymentResponse, PaymentUpdate,
    PaymentFeeCreate, PaymentFeeResponse, PaymentFeeUpdate
)
from dependency import get_db, get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: PaymentCreate,
    db: get_db,
    current_user: get_current_user
):
    # Get the student record for the current user
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=404,
            detail="Current user is not a student"
        )
    
    db_payment = PaymentTransaction(**payment.model_dump(), student_id=student.id)
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


@router.get("", response_model=List[PaymentResponse])
def get_all_payments(db: get_db):
    return db.query(PaymentTransaction).all()


@router.get("/me", response_model=List[PaymentResponse])
def get_my_payments(db: get_db, current_user: get_current_user):
    # Get the student record for the current user
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=404,
            detail="Current user is not a student"
        )
    
    return (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.student_id == student.id)
        .all()
    )

# PaymentFee CRUD APIs
@router.post("/fees", response_model=PaymentFeeResponse, status_code=status.HTTP_201_CREATED)
def create_payment_fee(
    payment_fee: PaymentFeeCreate,
    db: get_db,
    current_user: get_current_user
):

    db_payment_fee = PaymentFee(**payment_fee.model_dump())
    db.add(db_payment_fee)
    db.commit()
    db.refresh(db_payment_fee)
    return db_payment_fee


@router.get("/fees", response_model=List[PaymentFeeResponse])
def get_all_payment_fees(db: get_db):
    """Get all payment fees."""
    return db.query(PaymentFee).all()


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: get_db):
    payment = db.query(PaymentTransaction).filter(PaymentTransaction.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment transaction not found")
    return payment


@router.put("/{payment_id}", response_model=PaymentResponse)
def update_payment_status(
    payment_id: int,
    update_data: PaymentUpdate,
    db: get_db,
    current_user: get_current_user
):
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can update payment status"
        )

    payment = db.query(PaymentTransaction).filter(PaymentTransaction.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment transaction not found")

    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(payment, key, value)

    db.commit()
    db.refresh(payment)
    return payment


@router.get("/fees/program/{program_id}", response_model=List[PaymentFeeResponse])
def get_payment_fees_by_program(program_id: int, db: get_db):
    """Get all payment fees for a specific program."""
    return db.query(PaymentFee).filter(PaymentFee.program_id == program_id).all()


@router.get("/fees/{fee_id}", response_model=PaymentFeeResponse)
def get_payment_fee(fee_id: int, db: get_db):
    """Get a specific payment fee by ID."""
    fee = db.query(PaymentFee).filter(PaymentFee.id == fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Payment fee not found")
    return fee


@router.put("/fees/{fee_id}", response_model=PaymentFeeResponse)
def update_payment_fee(
    fee_id: int,
    update_data: PaymentFeeUpdate,
    db: get_db,
    current_user: get_current_user
):
    """Update a payment fee. Requires admin access."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can update payment fees"
        )

    fee = db.query(PaymentFee).filter(PaymentFee.id == fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Payment fee not found")

    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(fee, key, value)

    db.commit()
    db.refresh(fee)
    return fee


@router.delete("/fees/{fee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_fee(
    fee_id: int,
    db: get_db,
    current_user: get_current_user
):
    """Delete a payment fee. Requires admin access."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can delete payment fees"
        )

    fee = db.query(PaymentFee).filter(PaymentFee.id == fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Payment fee not found")

    db.delete(fee)
    db.commit()
    return

@router.get("/fees/me/unpaid", response_model=List[PaymentFeeResponse])
def get_my_unpaid_fees(db: get_db, current_user: get_current_user):
    """Get all unpaid payment fees for the current user if they are a student."""
    
    # Check if current user has a student record
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(
            status_code=404, 
            detail="Current user is not a student"
        )
    
    # Get all program IDs the student is enrolled in
    program_ids = [program.id for program in student.programs]
    
    if not program_ids:
        return []  # Student not enrolled in any programs
    
    # Get all payment fees for the student's programs
    all_fees = db.query(PaymentFee).filter(PaymentFee.program_id.in_(program_ids)).all()
    
    # Get all successful payments made by the current user for these programs
    paid_transactions = db.query(PaymentTransaction).filter(
        PaymentTransaction.student_id == student.id,
        PaymentTransaction.program_id.in_(program_ids),
        PaymentTransaction.status == StatusType.CONFIRMED
    ).all()
    
    paid_fee_signatures = set()
    for transaction in paid_transactions:
        paid_fee_signatures.add((transaction.program_id, transaction.amount))
    
    # Filter out fees that have been paid
    unpaid_fees = []
    for fee in all_fees:
        fee_signature = (fee.program_id, fee.amount)
        if fee_signature not in paid_fee_signatures:
            unpaid_fees.append(fee)
    
    return unpaid_fees


@router.get("/fees/student/{student_id}/unpaid", response_model=List[PaymentFeeResponse])
def get_student_unpaid_fees(student_id: int, db: get_db, current_user: get_current_user):
    """Get all unpaid payment fees for a specific student. Requires admin access."""
    
    # Check if current user is admin
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view fees for other students"
        )
    
    # Check if student exists
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=404, 
            detail="Student not found"
        )
    
    # Get all program IDs the student is enrolled in
    program_ids = [program.id for program in student.programs]
    
    if not program_ids:
        return []  # Student not enrolled in any programs
    
    # Get all payment fees for the student's programs
    all_fees = db.query(PaymentFee).filter(PaymentFee.program_id.in_(program_ids)).all()
    
    # Get all successful payments made by the student for these programs
    paid_transactions = db.query(PaymentTransaction).filter(
        PaymentTransaction.student_id == student.id,
        PaymentTransaction.program_id.in_(program_ids),
        PaymentTransaction.status == StatusType.CONFIRMED
    ).all()
    
    paid_fee_signatures = set()
    for transaction in paid_transactions:
        paid_fee_signatures.add((transaction.program_id, transaction.amount))
    
    # Filter out fees that have been paid
    unpaid_fees = []
    for fee in all_fees:
        fee_signature = (fee.program_id, fee.amount)
        if fee_signature not in paid_fee_signatures:
            unpaid_fees.append(fee)
    
    return unpaid_fees

