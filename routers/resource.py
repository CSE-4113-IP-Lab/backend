
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime

from models.resource import Equipment, EquipmentEntry, Booking
from models.enum import BookingType, StatusType
from models.user import User, UserRole
from dependency import get_db, get_current_user
from schemas.resource import (
    EquipmentCreate, EquipmentUpdate, EquipmentResponse,
    BookingCreate, BookingUpdate, BookingResponse
)


router = APIRouter(prefix="/equipment", tags=["equipment"])


# Helper Functions
def check_admin_or_staff(current_user: User):
    """Check if current user is admin or staff"""
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or staff can perform this action"
        )

def check_student_or_faculty(current_user: User):
    """Check if current user is student or faculty"""
    if current_user.role not in [UserRole.STUDENT, UserRole.FACULTY]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students or faculty can make bookings"
        )

def update_equipment_quantity(db: Session, equipment_id: int, quantity_change: int):
    """Update equipment available quantity"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment with id {equipment_id} not found"
        )
    
    # Check if we have enough quantity when reducing
    if quantity_change < 0 and equipment.available_quantity < abs(quantity_change):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient quantity available. Available: {equipment.available_quantity}, Requested: {abs(quantity_change)}"
        )


# Equipment Routes
@router.post("/", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
def add_equipment(
    equipment_data: EquipmentCreate,
    db: get_db,
    current_user: get_current_user

):
    """Add new equipment - Admin/Staff only"""
    check_admin_or_staff(current_user)
    
    # Check if equipment with same name already exists
    existing_equipment = db.query(Equipment).filter(Equipment.name == equipment_data.name).first()
    if existing_equipment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Equipment with this name already exists"
        )
    
    new_equipment = Equipment(**equipment_data.dict())
    db.add(new_equipment)
    db.commit()
    db.refresh(new_equipment)
    
    return new_equipment

@router.put("/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(
    equipment_id: int,
    equipment_data: EquipmentUpdate,
    db: get_db,
    current_user: get_current_user
):
    """Update equipment - Admin/Staff only"""
    check_admin_or_staff(current_user)
    
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )
    
    # Check if name already exists (if updating name)
    if equipment_data.name and equipment_data.name != equipment.name:
        existing_equipment = db.query(Equipment).filter(Equipment.name == equipment_data.name).first()
        if existing_equipment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Equipment with this name already exists"
            )
    
    # Update fields
    update_data = equipment_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(equipment, field, value)
    
    db.commit()
    db.refresh(equipment)
    
    return equipment

@router.get("/", response_model=List[EquipmentResponse])
def get_all_equipment(
    db: get_db,
    current_user: get_current_user
):
    """Get all equipment - Any authenticated user"""
    equipment_list = db.query(Equipment).options(joinedload(Equipment.entries)).all()
    
    # Calculate available quantity for each equipment
    for equipment in equipment_list:
        equipment.available_quantity = equipment.available_quantity
    
    return equipment_list

@router.get("/{equipment_id}", response_model=EquipmentResponse)
def get_equipment_details(
    equipment_id: int,
    db: get_db,
    current_user: get_current_user
):
    """Get equipment details - Any authenticated user"""
    equipment = db.query(Equipment).options(joinedload(Equipment.entries)).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )
    
    return equipment


# Booking Routes
@router.post("/booking", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_data: BookingCreate,
    db: get_db,
    current_user: get_current_user
):
    """Create booking - Student/Faculty only"""
    check_student_or_faculty(current_user)
    
    # Create booking
    booking = Booking(
        type=booking_data.type,
        start_time=booking_data.start_time,
        end_time=booking_data.end_time,
        date=booking_data.date,
        request_by_id=current_user.id
    )
    
    db.add(booking)
    db.flush()  # Get the booking ID
    
    # Process equipment entries
    for entry_data in booking_data.equipment_entries:
        equipment_id = entry_data["equipment_id"]
        quantity = entry_data["quantity"]
        
        # Check if equipment exists and has enough quantity
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Equipment with id {equipment_id} not found"
            )
        
        if equipment.available_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient quantity for {equipment.name}. Available: {equipment.available_quantity}, Requested: {quantity}"
            )
        
        # Create equipment entry
        equipment_entry = EquipmentEntry(
            equipment_id=equipment_id,
            booking_id=booking.id,
            quantity=quantity
        )
        db.add(equipment_entry)
    
    db.commit()
    db.refresh(booking)
    
    return booking

@router.put("/booking/{booking_id}", response_model=BookingResponse)
def update_booking(
    booking_id: int,
    booking_data: BookingUpdate,
    db: get_db,
    current_user: get_current_user
):
    """Update booking - Status by Admin/Staff, Cancel by requester"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check permissions
    if booking_data.status:
        if booking_data.status == StatusType.CANCELLED:
            # Only requester can cancel
            if booking.request_by_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the requester can cancel the booking"
                )
        else:
            # Only admin/staff can update status
            check_admin_or_staff(current_user)
    
    # If status is being changed to CANCELLED or FAILED, add quantities back
    if booking_data.status in [StatusType.CANCELLED, StatusType.FAILED]:
        if booking.status not in [StatusType.CANCELLED, StatusType.FAILED]:
            # Add quantities back to available stock
            for entry in booking.equipment_entries:
                equipment = db.query(Equipment).filter(Equipment.id == entry.equipment_id).first()
                if equipment:
                    # Remove the entry to make quantity available again
                    db.delete(entry)
    
    # Update booking fields
    update_data = booking_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)
    
    db.commit()
    db.refresh(booking)
    
    return booking

@router.get("/booking/", response_model=List[BookingResponse])
def get_user_bookings(
    db: get_db,
    current_user: get_current_user
):
    """Get current user's bookings"""
    bookings = db.query(Booking).filter(Booking.request_by_id == current_user.id).all()
    return bookings

@router.get("/booking/{booking_id}", response_model=BookingResponse)
def get_booking_details(
    booking_id: int,
    db: get_db,
    current_user: get_current_user
):
    """Get booking details - Own booking or Admin/Staff"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check if user can view this booking
    if booking.request_by_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own bookings"
        )
    
    return booking

@router.get("/booking/all/", response_model=List[BookingResponse])
def get_all_bookings(
    db: get_db,
    current_user: get_current_user
):
    """Get all bookings - Admin/Staff only"""
    check_admin_or_staff(current_user)
    
    bookings = db.query(Booking).all()
    return bookings