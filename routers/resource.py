from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime

from models.resource import Equipment, EquipmentEntry, Booking, EquipmentRequest
from models.enum import BookingType, StatusType, EquipmentRequestStatus
from models.user import User, UserRole
from models.file import File as FileModel
from dependency import get_db, get_current_user
from utils import upload_file, delete_file
from schemas.resource import (
    EquipmentCreate, EquipmentUpdate, EquipmentResponse,
    EquipmentRequestCreate, EquipmentRequestUpdate, EquipmentRequestResponse,
    BookingCreate, BookingUpdate, BookingResponse
)


router = APIRouter(prefix="/equipment", tags=["Equipment"])


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
    print(f"Current user role: {current_user.role}")
    if current_user.role not in [UserRole.STUDENT, UserRole.FACULTY]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students or faculty can make equipment requests"
        )

def update_equipment_availability(db: Session, equipment_id: int, quantity_change: int):
    """Update equipment available quantity"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment with id {equipment_id} not found"
        )
    
    new_available = equipment.available_quantity + quantity_change
    
    # Check if we have enough quantity when reducing
    if new_available < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient quantity available. Available: {equipment.available_quantity}, Requested: {abs(quantity_change)}"
        )
    
    equipment.available_quantity = new_available
    equipment.updated_at = datetime.utcnow()
    db.commit()
    return equipment


# Equipment Management Routes (Admin/Staff only)
@router.post("", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
def add_equipment(
    equipment_data: EquipmentCreate,
    db: get_db,
    current_user: get_current_user):

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
    new_equipment.available_quantity = new_equipment.quantity  # Set available = total initially
    db.add(new_equipment)
    db.commit()
    db.refresh(new_equipment)
    
    return new_equipment

@router.get("", response_model=List[EquipmentResponse])
def get_all_equipment(
    db: get_db,
    current_user: get_current_user
):
    """Get all equipment - Available to all authenticated users"""
    equipment_list = db.query(Equipment).all()
    return equipment_list

# Equipment Request Routes - Put these BEFORE /{equipment_id} route
@router.post("/request", response_model=EquipmentRequestResponse, status_code=status.HTTP_201_CREATED)
def create_equipment_request(
    request_data: EquipmentRequestCreate,
    db: get_db,
    current_user: get_current_user
):
    """Create equipment request - Students and Faculty"""
    check_student_or_faculty(current_user)
    
    # Check if equipment exists and has enough quantity
    equipment = db.query(Equipment).filter(Equipment.id == request_data.equipment_id).first()
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )
    
    if equipment.available_quantity < request_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient quantity available. Available: {equipment.available_quantity}, Requested: {request_data.quantity}"
        )
    
    # Create request
    new_request = EquipmentRequest(
        equipment_id=request_data.equipment_id,
        user_id=current_user.id,
        quantity=request_data.quantity,
        purpose=request_data.purpose
    )
    
    # Role-based approval logic
    if current_user.role == UserRole.FACULTY:
        # Faculty requests are automatically approved
        new_request.status = EquipmentRequestStatus.APPROVED
        new_request.approved_date = datetime.utcnow()
        new_request.approved_by_id = current_user.id  # Self-approved for faculty
        
        # Reduce available quantity immediately for faculty
        update_equipment_availability(db, request_data.equipment_id, -request_data.quantity)
        
    elif current_user.role == UserRole.STUDENT:
        # Student requests need admin approval, but quantity is reserved
        new_request.status = EquipmentRequestStatus.PENDING
        
        # Reduce available quantity for pending student requests too
        update_equipment_availability(db, request_data.equipment_id, -request_data.quantity)
    
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    
    # Load equipment relationship
    db.refresh(new_request)
    
    return new_request

@router.get("/requests", response_model=List[EquipmentRequestResponse])
def get_equipment_requests(
    db : get_db,
    current_user: get_current_user,
    status_filter: Optional[EquipmentRequestStatus] = None
):
    """Get equipment requests based on user role"""
    
    query = db.query(EquipmentRequest).options(joinedload(EquipmentRequest.equipment))
    
    if current_user.role in [UserRole.ADMIN, UserRole.STAFF]:
        # Admin/Staff can see all requests
        if status_filter:
            query = query.filter(EquipmentRequest.status == status_filter)
    else:
        # Students/Faculty only see their own requests
        query = query.filter(EquipmentRequest.user_id == current_user.id)
        if status_filter:
            query = query.filter(EquipmentRequest.status == status_filter)
    
    requests = query.order_by(EquipmentRequest.request_date.desc()).all()
    return requests

@router.get("/requests/{request_id}", response_model=EquipmentRequestResponse)
def get_equipment_request(
    request_id: int,
    db: get_db,
    current_user: get_current_user
):
    """Get specific equipment request"""
    
    request = db.query(EquipmentRequest).options(joinedload(EquipmentRequest.equipment)).filter(EquipmentRequest.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment request not found"
        )
    
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF] and request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own requests"
        )
    
    return request

@router.get("/{equipment_id}", response_model=EquipmentResponse)
def get_equipment(
    equipment_id: int,
    db: get_db,
    current_user: get_current_user
):
    """Get specific equipment - Available to all authenticated users"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )
    return equipment

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
        existing = db.query(Equipment).filter(Equipment.name == equipment_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Equipment with this name already exists"
            )
    
    # Handle relative quantity changes
    update_data = equipment_data.dict(exclude_unset=True, exclude={"image_id"})
    
    if "quantity" in update_data:
        quantity_change = update_data["quantity"]
        old_quantity = equipment.quantity
        old_available = equipment.available_quantity
        
        # Calculate new total quantity (relative change)
        new_total_quantity = old_quantity + quantity_change
        
        # Ensure new total quantity is not negative
        if new_total_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid quantity change. Current quantity: {old_quantity}, Change: {quantity_change}. Result would be negative."
            )
        
        # Calculate how much available quantity changes
        # If we're increasing total (+10), available also increases by 10
        # If we're decreasing total (-5), available also decreases by 5 (if possible)
        new_available_quantity = old_available + quantity_change
        
        # Ensure available quantity doesn't go negative
        if new_available_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reduce quantity. Current available: {old_available}, Change: {quantity_change}. Would result in negative available quantity."
            )
        
        # Update both quantities
        equipment.quantity = new_total_quantity
        equipment.available_quantity = new_available_quantity
        
        # Remove quantity from update_data since we handled it manually
        del update_data["quantity"]
    
    # Update other equipment fields, excluding image_id (handle images separately via image endpoints)
    for field, value in update_data.items():
        setattr(equipment, field, value)
    
    equipment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(equipment)
    
    return equipment

@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(
    equipment_id: int,
    db: get_db,
    current_user: get_current_user
):
    """Delete equipment - Admin/Staff only"""
    check_admin_or_staff(current_user)
    
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )
    
    # Check if equipment has pending requests
    pending_requests = db.query(EquipmentRequest).filter(
        EquipmentRequest.equipment_id == equipment_id,
        EquipmentRequest.status.in_([EquipmentRequestStatus.PENDING, EquipmentRequestStatus.APPROVED, EquipmentRequestStatus.HANDOVER])
    ).first()
    
    if pending_requests:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete equipment with pending requests"
        )
    
    db.delete(equipment)
    db.commit()

# Equipment Request Management Routes (Admin/Staff only)
@router.put("/requests/{request_id}/approve", response_model=EquipmentRequestResponse)
def approve_equipment_request(
    request_id: int,
    db: get_db,
    current_user: get_current_user
):
    """Approve equipment request - Admin/Staff only"""
    check_admin_or_staff(current_user)
    
    request = db.query(EquipmentRequest).filter(EquipmentRequest.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment request not found"
        )
    
    if request.status != EquipmentRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending requests can be approved"
        )
    
    request.status = EquipmentRequestStatus.APPROVED
    request.approved_date = datetime.utcnow()
    request.approved_by_id = current_user.id
    
    db.commit()
    db.refresh(request)
    
    return request

@router.put("/requests/{request_id}/reject", response_model=EquipmentRequestResponse)
def reject_equipment_request(
    request_id: int,
    db: get_db,
    notes: str ,
    current_user: get_current_user
):
    """Reject equipment request - Admin/Staff only"""
    check_admin_or_staff(current_user)
    
    request = db.query(EquipmentRequest).filter(EquipmentRequest.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment request not found"
        )
    
    if request.status != EquipmentRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending requests can be rejected"
        )
    
    # Return quantity to available pool
    update_equipment_availability(db, request.equipment_id, request.quantity)
    
    request.status = EquipmentRequestStatus.REJECTED
    request.notes = notes
    request.approved_by_id = current_user.id
    
    db.commit()
    db.refresh(request)
    
    return request

@router.put("/requests/{request_id}/handover", response_model=EquipmentRequestResponse)
def handover_equipment(
    request_id: int,
    db: get_db,
    current_user: get_current_user
):
    """Mark equipment as handed over - Admin/Staff only"""
    check_admin_or_staff(current_user)
    
    request = db.query(EquipmentRequest).filter(EquipmentRequest.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment request not found"
        )
    
    if request.status != EquipmentRequestStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only approved requests can be handed over"
        )
    
    request.status = EquipmentRequestStatus.HANDOVER
    request.handover_date = datetime.utcnow()
    
    db.commit()
    db.refresh(request)
    
    return request

@router.put("/requests/{request_id}/return", response_model=EquipmentRequestResponse)
def return_equipment(
    request_id: int,
    db: get_db,
    current_user: get_current_user
):
    """Mark equipment as returned/completed - Student or Admin/Staff"""
    
    request = db.query(EquipmentRequest).filter(EquipmentRequest.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment request not found"
        )
    
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF] and request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only return your own equipment"
        )
    
    if request.status != EquipmentRequestStatus.HANDOVER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only handed over equipment can be returned"
        )
    
    # Return quantity to available pool
    update_equipment_availability(db, request.equipment_id, request.quantity)
    
    request.status = EquipmentRequestStatus.COMPLETED
    request.return_date = datetime.utcnow()
    
    db.commit()
    db.refresh(request)
    
    return request

@router.put("/requests/{request_id}/cancel", response_model=EquipmentRequestResponse)
def cancel_equipment_request(
    request_id: int,
    db: get_db,
    current_user: get_current_user
):
    """Cancel equipment request - Student or Admin/Staff"""
    
    request = db.query(EquipmentRequest).filter(EquipmentRequest.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment request not found"
        )
    
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF] and request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own requests"
        )
    
    if request.status not in [EquipmentRequestStatus.PENDING, EquipmentRequestStatus.APPROVED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending or approved requests can be cancelled"
        )
    
    # Return quantity to available pool
    update_equipment_availability(db, request.equipment_id, request.quantity)
    
    request.status = EquipmentRequestStatus.CANCELLED
    
    db.commit()
    db.refresh(request)
    
    return request


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

@router.get("/get_booking", response_model=List[BookingResponse])
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

@router.get("/booking/all", response_model=List[BookingResponse])
def get_all_bookings(
    db: get_db,
    current_user: get_current_user
):
    """Get all bookings - Admin/Staff only"""
    check_admin_or_staff(current_user)
    
    bookings = db.query(Booking).all()
    return bookings

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


# Equipment Image Upload Routes
@router.post("/{equipment_id}/image", response_model=EquipmentResponse)
async def add_equipment_image(
    equipment_id: int, 
    db: get_db, 
    current_user: get_current_user,
    file: UploadFile = File(...)
):
    """Add image to equipment - Admin/Staff only"""
    check_admin_or_staff(current_user)
    
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    
    # Upload new image
    uploaded_file = await upload_file(db, "equipment", file)
    if not uploaded_file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to upload image")
    
    # Remove old image if exists
    if equipment.image_id:
        delete_file(db, equipment.image_id)
    
    # Set new image
    equipment.image_id = uploaded_file.id
    equipment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(equipment)
    
    return equipment

@router.delete("/{equipment_id}/image", response_model=EquipmentResponse)
def remove_equipment_image(
    equipment_id: int, 
    db: get_db, 
    current_user: get_current_user
):
    """Remove image from equipment - Admin/Staff only"""
    check_admin_or_staff(current_user)
    
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    
    if not equipment.image_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No image found for this equipment")
    
    # Delete the image file
    delete_file(db, equipment.image_id)
    
    # Remove image reference
    equipment.image_id = None
    equipment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(equipment)
    
    return equipment
