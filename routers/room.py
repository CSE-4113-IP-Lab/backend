from fastapi import APIRouter, HTTPException, status
from sqlalchemy import and_, or_, not_
from sqlalchemy.orm import Session  # Keep for helper function
from typing import List, Optional
from datetime import datetime, timedelta, time, date
from dependency import get_current_user, get_db
from models.room import Room, RoomBooking, TimeSlot
from models.user import User, UserRole
from models.enum import RoomStatus, RoomBookingStatus
from schemas.room import (
    RoomResponse, RoomCreate, RoomUpdate,
    RoomBookingResponse, RoomBookingCreate, RoomBookingUpdate,
    AvailableRoomsRequest, BookRoomRequest, TimeSlotInfo
)

router = APIRouter(prefix="/rooms", tags=["Rooms"])


# Helper Functions
def check_admin_role(current_user: User):
    """Check if current user is admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform this action"
        )

def check_faculty_or_admin(current_user: User):
    """Check if current user is faculty or admin"""
    if current_user.role not in [UserRole.FACULTY, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only faculty and administrators can book rooms"
        )


# Room Management Endpoints (Admin only)
@router.post("/", response_model=RoomResponse)
def create_room(
    room: RoomCreate,
    db: get_db,
    current_user: get_current_user
):
    check_admin_role(current_user)
    
    # Check if room number already exists
    existing_room = db.query(Room).filter(Room.room_number == room.room_number).first()
    if existing_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room number already exists"
        )
    
    db_room = Room(**room.dict())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


@router.get("/", response_model=List[RoomResponse])
def get_all_rooms(
    db: get_db,
    current_user: get_current_user,
    skip: int = 0,
    limit: int = 100,
    status: Optional[RoomStatus] = None,
    purpose: Optional[str] = None
):
    query = db.query(Room)
    
    if status:
        query = query.filter(Room.status == status)
    
    if purpose:
        query = query.filter(Room.purpose.ilike(f"%{purpose}%"))
    
    rooms = query.offset(skip).limit(limit).all()
    
    # Add available slots for each room for today
    today = date.today()
    for room in rooms:
        room.available_slots = get_available_slots_for_room(db, room.id, today)
    
    return rooms


@router.get("/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: int,
    db: get_db,
    current_user: get_current_user
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Add available slots for today
    today = date.today()
    room.available_slots = get_available_slots_for_room(db, room.id, today)
    
    return room


@router.put("/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    room_update: RoomUpdate,
    db: get_db,
    current_user: get_current_user
):
    check_admin_role(current_user)
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    update_data = room_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(room, field, value)
    
    db.commit()
    db.refresh(room)
    return room


# Room Availability and Booking Endpoints
@router.get("/available/search")
def get_available_rooms(
    start_datetime: datetime,
    end_datetime: datetime,
    db: get_db,
    current_user: get_current_user,
    purpose: Optional[str] = None,
    capacity: Optional[int] = None
):
    """Get available rooms for a specific time period"""
    
    # Validate time range
    if end_datetime <= start_datetime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )
    
    # Check if the time is within operating hours (8 AM to 8 PM)
    start_time = start_datetime.time()
    end_time = end_datetime.time()
    
    if start_time < time(8, 0) or end_time > time(20, 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rooms are only available between 8:00 AM and 8:00 PM"
        )
    
    # Base query for available rooms
    query = db.query(Room).filter(Room.status == RoomStatus.AVAILABLE)
    
    if purpose:
        query = query.filter(Room.purpose.ilike(f"%{purpose}%"))
    
    if capacity:
        query = query.filter(Room.capacity >= capacity)
    
    # Get rooms that don't have conflicting bookings
    conflicting_bookings = db.query(RoomBooking.room_id).filter(
        and_(
            RoomBooking.status.in_([RoomBookingStatus.SCHEDULED, RoomBookingStatus.ONGOING]),
            or_(
                and_(
                    RoomBooking.start_datetime <= start_datetime,
                    RoomBooking.end_datetime > start_datetime
                ),
                and_(
                    RoomBooking.start_datetime < end_datetime,
                    RoomBooking.end_datetime >= end_datetime
                ),
                and_(
                    RoomBooking.start_datetime >= start_datetime,
                    RoomBooking.end_datetime <= end_datetime
                )
            )
        )
    ).subquery()
    
    available_rooms = query.filter(not_(Room.id.in_(conflicting_bookings))).all()
    
    # Add available slots for each room
    for room in available_rooms:
        room.available_slots = get_available_slots_for_room(
            db, room.id, start_datetime.date()
        )
    
    return available_rooms


@router.get("/{room_id}/slots")
def get_room_available_slots(
    room_id: int,
    date: date,
    db: get_db,
    current_user: get_current_user
):
    """Get available time slots for a specific room on a specific date"""
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    slots = get_available_slots_for_room(db, room_id, date)
    return {"room_id": room_id, "date": date, "available_slots": slots}


def get_available_slots_for_room(db: Session, room_id: int, date: date) -> List[TimeSlotInfo]:
    """Helper function to get available time slots for a room on a specific date"""
    
    # Operating hours: 8 AM to 8 PM
    start_of_day = datetime.combine(date, time(8, 0))
    end_of_day = datetime.combine(date, time(20, 0))
    
    # Get all bookings for this room on this date
    bookings = db.query(RoomBooking).filter(
        and_(
            RoomBooking.room_id == room_id,
            RoomBooking.status.in_([RoomBookingStatus.SCHEDULED, RoomBookingStatus.ONGOING]),
            RoomBooking.start_datetime >= start_of_day,
            RoomBooking.start_datetime < end_of_day + timedelta(days=1)
        )
    ).order_by(RoomBooking.start_datetime).all()
    
    available_slots = []
    current_time = start_of_day
    
    for booking in bookings:
        # Add slot before this booking if there's a gap
        if current_time < booking.start_datetime:
            available_slots.append(TimeSlotInfo(
                start_datetime=current_time,
                end_datetime=booking.start_datetime,
                is_available=True
            ))
        
        # Move current time to end of this booking
        current_time = max(current_time, booking.end_datetime)
    
    # Add final slot if there's time left in the day
    if current_time < end_of_day:
        available_slots.append(TimeSlotInfo(
            start_datetime=current_time,
            end_datetime=end_of_day,
            is_available=True
        ))
    
    return available_slots


# Booking Management Endpoints
@router.post("/book", response_model=RoomBookingResponse)
def book_room(
    booking_request: BookRoomRequest,
    db: get_db,
    current_user: get_current_user
):
    """Book a room for a specific time period"""
    
    # Only faculty and admin can book rooms
    check_faculty_or_admin(current_user)
    
    # Check if room exists
    room = db.query(Room).filter(Room.id == booking_request.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Calculate end time
    end_datetime = booking_request.start_datetime + timedelta(
        hours=booking_request.duration_hours,
        minutes=booking_request.duration_minutes
    )
    
    # Validate time range
    start_time = booking_request.start_datetime.time()
    end_time = end_datetime.time()
    
    if start_time < time(8, 0) or end_time > time(20, 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rooms are only available between 8:00 AM and 8:00 PM"
        )
    
    # Check for conflicts
    conflicting_booking = db.query(RoomBooking).filter(
        and_(
            RoomBooking.room_id == booking_request.room_id,
            RoomBooking.status.in_([RoomBookingStatus.SCHEDULED, RoomBookingStatus.ONGOING]),
            or_(
                and_(
                    RoomBooking.start_datetime <= booking_request.start_datetime,
                    RoomBooking.end_datetime > booking_request.start_datetime
                ),
                and_(
                    RoomBooking.start_datetime < end_datetime,
                    RoomBooking.end_datetime >= end_datetime
                ),
                and_(
                    RoomBooking.start_datetime >= booking_request.start_datetime,
                    RoomBooking.end_datetime <= end_datetime
                )
            )
        )
    ).first()
    
    if conflicting_booking:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Room is already booked for the requested time period"
        )
    
    # Create booking
    booking_data = {
        "room_id": booking_request.room_id,
        "user_id": current_user.id,
        "purpose": booking_request.purpose,
        "start_datetime": booking_request.start_datetime,
        "end_datetime": end_datetime,
        "notes": booking_request.notes,
        "status": RoomBookingStatus.SCHEDULED
    }
    
    # Auto-approve for admin, faculty might need approval based on business rules
    if current_user.role == UserRole.ADMIN:
        booking_data["approved_by_id"] = current_user.id
        booking_data["approved_at"] = datetime.utcnow()
    
    db_booking = RoomBooking(**booking_data)
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    return db_booking


@router.get("/bookings/", response_model=List[RoomBookingResponse])
def get_bookings(
    db: get_db,
    current_user: get_current_user,
    skip: int = 0,
    limit: int = 100,
    room_id: Optional[int] = None,
    user_id: Optional[int] = None,
    status: Optional[RoomBookingStatus] = None
):
    """Get room bookings"""
    
    query = db.query(RoomBooking)
    
    # Non-admin users can only see their own bookings
    if current_user.role != UserRole.ADMIN:
        query = query.filter(RoomBooking.user_id == current_user.id)
    elif user_id:
        query = query.filter(RoomBooking.user_id == user_id)
    
    if room_id:
        query = query.filter(RoomBooking.room_id == room_id)
    
    if status:
        query = query.filter(RoomBooking.status == status)
    
    bookings = query.order_by(RoomBooking.start_datetime.desc()).offset(skip).limit(limit).all()
    
    # Add related data
    for booking in bookings:
        booking.room = db.query(Room).filter(Room.id == booking.room_id).first()
        booking.user_name = db.query(User).filter(User.id == booking.user_id).first().email
        if booking.approved_by_id:
            approved_by = db.query(User).filter(User.id == booking.approved_by_id).first()
            booking.approved_by_name = approved_by.email if approved_by else None
    
    return bookings


@router.get("/bookings/{booking_id}", response_model=RoomBookingResponse)
def get_booking(
    booking_id: int,
    db: get_db,
    current_user: get_current_user
):
    """Get a specific booking"""
    
    booking = db.query(RoomBooking).filter(RoomBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own bookings"
        )
    
    return booking


@router.put("/bookings/{booking_id}/cancel")
def cancel_booking(
    booking_id: int,
    db: get_db,
    current_user: get_current_user
):
    """Cancel a room booking"""
    
    booking = db.query(RoomBooking).filter(RoomBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.ADMIN and booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own bookings"
        )
    
    # Can only cancel scheduled bookings
    if booking.status != RoomBookingStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only scheduled bookings can be cancelled"
        )
    
    booking.status = RoomBookingStatus.CANCELLED
    db.commit()
    
    return {"message": "Booking cancelled successfully"}


@router.put("/bookings/{booking_id}/approve")
def approve_booking(
    booking_id: int,
    db: get_db,
    current_user: get_current_user
):
    """Approve a room booking (Admin only)"""
    
    check_admin_role(current_user)
    
    booking = db.query(RoomBooking).filter(RoomBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    booking.approved_by_id = current_user.id
    booking.approved_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Booking approved successfully"}
