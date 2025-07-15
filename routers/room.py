from fastapi import APIRouter, HTTPException, status
from sqlalchemy import and_, or_, not_, delete
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, time, date
from dependency import get_current_user, get_db
from models.room import Room, RoomBooking, RoomTimeSlot
from models.user import User, UserRole
from models.enum import RoomStatus, RoomBookingStatus
from schemas.room import (
    RoomResponse, RoomCreate, RoomUpdate,
    RoomBookingResponse, RoomBookingCreate, RoomBookingUpdate,
    AvailableRoomsRequest, BookRoomRequest, 
    RoomTimeSlotInfo, DaySchedule, WeeklySchedule,
    SlotAvailabilityRequest
)
from room_utils.slot_manager import SlotManager

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


def calculate_day_offset(target_date: date) -> int:
    """Calculate day offset (0-6) from today"""
    today = date.today()
    offset = (target_date - today).days
    if offset < 0 or offset > 6:
        raise ValueError(f"Date must be within next 7 days (today to day 6)")
    return offset


def generate_time_slots_for_room(db: Session, room: Room, target_date: date = None) -> None:
    """Generate 30-minute time slots for a room for the next 7 days"""
    if target_date is None:
        target_date = date.today()
    
    for day_offset in range(7):
        slot_date = target_date + timedelta(days=day_offset)
        
        # Clear existing slots for this date
        db.query(RoomTimeSlot).filter(
            and_(
                RoomTimeSlot.room_id == room.id,
                RoomTimeSlot.slot_date == slot_date
            )
        ).delete()
        
        # Generate 30-minute slots from operating start to end time
        current_time = room.operating_start_time
        end_time = room.operating_end_time
        
        while current_time < end_time:
            slot = RoomTimeSlot(
                room_id=room.id,
                day_offset=day_offset,
                slot_date=slot_date,
                slot_time=current_time,
                is_available=True
            )
            db.add(slot)
            
            # Move to next 30-minute slot
            current_datetime = datetime.combine(slot_date, current_time)
            next_datetime = current_datetime + timedelta(minutes=30)
            current_time = next_datetime.time()
    
    db.commit()


def initialize_slots_for_new_room(db: Session, room: Room) -> None:
    """Initialize time slots when a new room is created"""
    generate_time_slots_for_room(db, room)


def roll_daily_slots(db: Session) -> None:
    """Roll slots forward daily - remove yesterday's slots and add new day 7 slots"""
    today = date.today()
    yesterday = today - timedelta(days=1)
    day_7 = today + timedelta(days=6)
    
    # Remove yesterday's slots
    db.query(RoomTimeSlot).filter(RoomTimeSlot.slot_date == yesterday).delete()
    
    # Get all rooms and generate slots for day 7
    rooms = db.query(Room).all()
    for room in rooms:
        current_time = room.operating_start_time
        end_time = room.operating_end_time
        
        while current_time < end_time:
            slot = RoomTimeSlot(
                room_id=room.id,
                day_offset=6,  # Day 7 becomes new day 6
                slot_date=day_7,
                slot_time=current_time,
                is_available=True
            )
            db.add(slot)
            
            # Move to next 30-minute slot
            current_datetime = datetime.combine(day_7, current_time)
            next_datetime = current_datetime + timedelta(minutes=30)
            current_time = next_datetime.time()
    
    # Update day_offset for remaining slots
    db.query(RoomTimeSlot).filter(RoomTimeSlot.slot_date >= today).update({
        RoomTimeSlot.day_offset: RoomTimeSlot.day_offset - 1
    })
    
    db.commit()


def get_weekly_schedule_for_room(db: Session, room_id: int) -> WeeklySchedule:
    """Get the complete 7-day schedule for a room"""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    today = date.today()
    week_schedule = []
    
    for day_offset in range(7):
        slot_date = today + timedelta(days=day_offset)
        
        # Get all slots for this day
        slots = db.query(RoomTimeSlot).filter(
            and_(
                RoomTimeSlot.room_id == room_id,
                RoomTimeSlot.day_offset == day_offset,
                RoomTimeSlot.slot_date == slot_date
            )
        ).order_by(RoomTimeSlot.slot_time).all()
        
        slot_infos = [
            RoomTimeSlotInfo(
                day_offset=slot.day_offset,
                slot_date=slot.slot_date,
                slot_time=slot.slot_time,
                is_available=slot.is_available,
                booking_id=slot.booking_id
            ) for slot in slots
        ]
        
        day_schedule = DaySchedule(
            day_offset=day_offset,
            date=slot_date,
            slots=slot_infos
        )
        week_schedule.append(day_schedule)
    
    return WeeklySchedule(
        room_id=room_id,
        room_number=room.room_number,
        week_schedule=week_schedule
    )


def calculate_duration_slots(start_time: time, end_time: time) -> int:
    """Calculate number of 30-minute slots between start and end time"""
    start_datetime = datetime.combine(date.today(), start_time)
    end_datetime = datetime.combine(date.today(), end_time)
    duration_minutes = (end_datetime - start_datetime).total_seconds() / 60
    return int(duration_minutes / 30)


def mark_slots_as_booked(db: Session, room_id: int, booking_date: date, 
                        start_time: time, end_time: time, booking_id: int) -> None:
    """Mark time slots as booked for a reservation"""
    day_offset = calculate_day_offset(booking_date)
    
    # Get all slots that need to be marked as booked
    current_time = start_time
    while current_time < end_time:
        slot = db.query(RoomTimeSlot).filter(
            and_(
                RoomTimeSlot.room_id == room_id,
                RoomTimeSlot.day_offset == day_offset,
                RoomTimeSlot.slot_date == booking_date,
                RoomTimeSlot.slot_time == current_time
            )
        ).first()
        
        if slot:
            slot.is_available = False
            slot.booking_id = booking_id
        
        # Move to next 30-minute slot
        current_datetime = datetime.combine(booking_date, current_time)
        next_datetime = current_datetime + timedelta(minutes=30)
        current_time = next_datetime.time()
    
    db.commit()


def mark_slots_as_available(db: Session, room_id: int, booking_date: date,
                           start_time: time, end_time: time) -> None:
    """Mark time slots as available when booking is cancelled"""
    day_offset = calculate_day_offset(booking_date)
    
    # Get all slots that need to be marked as available
    current_time = start_time
    while current_time < end_time:
        slot = db.query(RoomTimeSlot).filter(
            and_(
                RoomTimeSlot.room_id == room_id,
                RoomTimeSlot.day_offset == day_offset,
                RoomTimeSlot.slot_date == booking_date,
                RoomTimeSlot.slot_time == current_time
            )
        ).first()
        
        if slot:
            slot.is_available = True
            slot.booking_id = None
        
        # Move to next 30-minute slot
        current_datetime = datetime.combine(booking_date, current_time)
        next_datetime = current_datetime + timedelta(minutes=30)
        current_time = next_datetime.time()
    
    db.commit()


def check_slots_availability(db: Session, room_id: int, booking_date: date,
                           start_time: time, end_time: time) -> bool:
    """Check if all required slots are available for booking"""
    day_offset = calculate_day_offset(booking_date)
    
    current_time = start_time
    while current_time < end_time:
        slot = db.query(RoomTimeSlot).filter(
            and_(
                RoomTimeSlot.room_id == room_id,
                RoomTimeSlot.day_offset == day_offset,
                RoomTimeSlot.slot_date == booking_date,
                RoomTimeSlot.slot_time == current_time,
                RoomTimeSlot.is_available == True
            )
        ).first()
        
        if not slot:
            return False
        
        # Move to next 30-minute slot
        current_datetime = datetime.combine(booking_date, current_time)
        next_datetime = current_datetime + timedelta(minutes=30)
        current_time = next_datetime.time()
    
    return True


# Room Management Endpoints (Admin only)
@router.post("/", response_model=RoomResponse)
def create_room(
    room: RoomCreate,
    db: get_db,
    current_user: get_current_user
):
    """Create a new room and initialize its time slots"""
    check_admin_role(current_user)
    
    # Check if room number already exists
    existing_room = db.query(Room).filter(Room.room_number == room.room_number).first()
    if existing_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room number already exists"
        )
    
    # Create room
    db_room = Room(**room.dict())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    
    # Initialize time slots for the next 7 days
    initialize_slots_for_new_room(db, db_room)
    
    # Get weekly schedule
    weekly_schedule = get_weekly_schedule_for_room(db, db_room.id)
    
    response = RoomResponse(**db_room.__dict__)
    response.weekly_schedule = weekly_schedule
    return response


@router.get("/", response_model=List[RoomResponse])
def get_all_rooms(
    db: get_db,
    current_user: get_current_user,
    skip: int = 0,
    limit: int = 100,
    status: Optional[RoomStatus] = None,
    purpose: Optional[str] = None,
    include_schedule: bool = False
):
    """Get all rooms with optional filtering"""
    query = db.query(Room)
    
    if status:
        query = query.filter(Room.status == status)
    
    if purpose:
        query = query.filter(Room.purpose.ilike(f"%{purpose}%"))
    
    rooms = query.offset(skip).limit(limit).all()
    
    response_rooms = []
    for room in rooms:
        room_response = RoomResponse(**room.__dict__)
        if include_schedule:
            room_response.weekly_schedule = get_weekly_schedule_for_room(db, room.id)
        response_rooms.append(room_response)
    
    return response_rooms


@router.get("/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: int,
    db: get_db,
    current_user: get_current_user,
    include_schedule: bool = True
):
    """Get a specific room with its weekly schedule"""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    room_response = RoomResponse(**room.__dict__)
    if include_schedule:
        room_response.weekly_schedule = get_weekly_schedule_for_room(db, room_id)
    
    return room_response


@router.put("/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    room_update: RoomUpdate,
    db: get_db,
    current_user: get_current_user
):
    """Update a room and regenerate slots if operating hours changed"""
    check_admin_role(current_user)
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Check if operating hours are being updated
    hours_changed = False
    update_data = room_update.dict(exclude_unset=True)
    
    if 'operating_start_time' in update_data or 'operating_end_time' in update_data:
        hours_changed = True
    
    # Update room
    for field, value in update_data.items():
        setattr(room, field, value)
    
    db.commit()
    db.refresh(room)
    
    # Regenerate slots if operating hours changed
    if hours_changed:
        # Cancel all existing bookings for this room (as schedule changed)
        bookings = db.query(RoomBooking).filter(
            and_(
                RoomBooking.room_id == room_id,
                RoomBooking.status == RoomBookingStatus.SCHEDULED
            )
        ).all()
        
        for booking in bookings:
            booking.status = RoomBookingStatus.CANCELLED
        
        # Regenerate all slots
        generate_time_slots_for_room(db, room)
    
    room_response = RoomResponse(**room.__dict__)
    room_response.weekly_schedule = get_weekly_schedule_for_room(db, room_id)
    
    return room_response


@router.delete("/{room_id}")
def delete_room(
    room_id: int,
    db: get_db,
    current_user: get_current_user
):
    """Delete a room and all its associated data"""
    check_admin_role(current_user)
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Cancel all active bookings
    active_bookings = db.query(RoomBooking).filter(
        and_(
            RoomBooking.room_id == room_id,
            RoomBooking.status.in_([RoomBookingStatus.SCHEDULED, RoomBookingStatus.ONGOING])
        )
    ).all()
    
    for booking in active_bookings:
        booking.status = RoomBookingStatus.CANCELLED
    
    # Delete the room (slots will be deleted via cascade)
    db.delete(room)
    db.commit()
    
    return {"message": "Room deleted successfully"}


# Weekly Schedule Endpoints
@router.get("/{room_id}/schedule", response_model=WeeklySchedule)
def get_room_weekly_schedule(
    room_id: int,
    db: get_db,
    current_user: get_current_user
):
    """Get the complete 7-day schedule for a room"""
    return get_weekly_schedule_for_room(db, room_id)


@router.get("/{room_id}/schedule/{day_offset}", response_model=DaySchedule)
def get_room_day_schedule(
    room_id: int,
    day_offset: int,
    db: get_db,
    current_user: get_current_user
):
    """Get the schedule for a specific day (0-6)"""
    if day_offset < 0 or day_offset > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Day offset must be between 0 and 6"
        )
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    today = date.today()
    slot_date = today + timedelta(days=day_offset)
    
    slots = db.query(RoomTimeSlot).filter(
        and_(
            RoomTimeSlot.room_id == room_id,
            RoomTimeSlot.day_offset == day_offset,
            RoomTimeSlot.slot_date == slot_date
        )
    ).order_by(RoomTimeSlot.slot_time).all()
    
    slot_infos = [
        RoomTimeSlotInfo(
            day_offset=slot.day_offset,
            slot_date=slot.slot_date,
            slot_time=slot.slot_time,
            is_available=slot.is_available,
            booking_id=slot.booking_id
        ) for slot in slots
    ]
    
    return DaySchedule(
        day_offset=day_offset,
        date=slot_date,
        slots=slot_infos
    )


# Available Rooms Search
@router.post("/search/available")
def search_available_rooms(
    search_request: AvailableRoomsRequest,
    db: get_db,
    current_user: get_current_user
):
    """Search for available rooms for a specific time period"""
    
    # Validate booking date is within 7 days
    try:
        day_offset = calculate_day_offset(search_request.booking_date)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Validate operating hours
    if (search_request.start_time < time(8, 0) or 
        search_request.end_time > time(20, 0)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search time must be within operating hours (8:00 AM - 8:00 PM)"
        )
    
    # Base query for rooms
    query = db.query(Room).filter(Room.status == RoomStatus.AVAILABLE)
    
    if search_request.purpose:
        query = query.filter(Room.purpose.ilike(f"%{search_request.purpose}%"))
    
    if search_request.capacity:
        query = query.filter(Room.capacity >= search_request.capacity)
    
    all_rooms = query.all()
    available_rooms = []
    
    # Check availability for each room
    for room in all_rooms:
        if check_slots_availability(
            db, room.id, search_request.booking_date,
            search_request.start_time, search_request.end_time
        ):
            available_rooms.append({
                "id": room.id,
                "room_number": room.room_number,
                "purpose": room.purpose,
                "capacity": room.capacity,
                "location": room.location,
                "description": room.description
            })
    
    return {
        "booking_date": search_request.booking_date,
        "start_time": search_request.start_time,
        "end_time": search_request.end_time,
        "available_rooms": available_rooms
    }


# Booking Management Endpoints
@router.post("/book")
def book_room(
    booking_request: BookRoomRequest,
    db: get_db,
    current_user: get_current_user
):
    """Book a room for a specific time period"""
    
    try:
        # Only faculty and admin can book rooms
        check_faculty_or_admin(current_user)
        
        # Check if room exists
        room = db.query(Room).filter(Room.id == booking_request.room_id).first()
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found"
            )
        
        # Validate room is available for booking
        if room.status != RoomStatus.AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Room is not available for booking"
            )
        
        # Check if all required slots are available
        if not check_slots_availability(
            db, booking_request.room_id, booking_request.booking_date,
            booking_request.start_time, booking_request.end_time
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="One or more time slots are not available"
            )
        
        # Calculate duration in slots
        duration_slots = calculate_duration_slots(
            booking_request.start_time, booking_request.end_time
        )
        
        # Create booking
        booking_data = {
            "room_id": booking_request.room_id,
            "user_id": current_user.id,
            "purpose": booking_request.purpose,
            "booking_date": booking_request.booking_date,
            "start_time": booking_request.start_time,
            "end_time": booking_request.end_time,
            "duration_slots": duration_slots,
            "notes": booking_request.notes,
            "status": RoomBookingStatus.SCHEDULED
        }
        
        # Auto-approve for all users (no approval required)
        booking_data["approved_by_id"] = current_user.id
        booking_data["approved_at"] = datetime.utcnow()
        
        db_booking = RoomBooking(**booking_data)
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        
        # Mark slots as booked
        mark_slots_as_booked(
            db, booking_request.room_id, booking_request.booking_date,
            booking_request.start_time, booking_request.end_time, db_booking.id
        )
        
        # Return simple response
        return {
            "id": db_booking.id,
            "room_id": db_booking.room_id,
            "user_id": db_booking.user_id,
            "purpose": db_booking.purpose,
            "booking_date": db_booking.booking_date.isoformat(),
            "start_time": db_booking.start_time.isoformat(),
            "end_time": db_booking.end_time.isoformat(),
            "duration_slots": db_booking.duration_slots,
            "status": db_booking.status.value,
            "notes": db_booking.notes,
            "created_at": db_booking.created_at.isoformat(),
            "approved_by_id": db_booking.approved_by_id,
            "approved_at": db_booking.approved_at.isoformat() if db_booking.approved_at else None,
            "message": "Room booked successfully"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during booking: {str(e)}"
        )


@router.get("/bookings/")
def get_bookings(
    db: get_db,
    current_user: get_current_user,
    skip: int = 0,
    limit: int = 100,
    room_id: Optional[int] = None,
    user_id: Optional[int] = None,
    status: Optional[RoomBookingStatus] = None,
    booking_date: Optional[date] = None
):
    """Get room bookings with filtering"""
    
    try:
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
        
        if booking_date:
            query = query.filter(RoomBooking.booking_date == booking_date)
        
        bookings = query.order_by(RoomBooking.created_at.desc()).offset(skip).limit(limit).all()
        
        # Convert to simple dict format
        result = []
        for booking in bookings:
            result.append({
                "id": booking.id,
                "room_id": booking.room_id,
                "user_id": booking.user_id,
                "purpose": booking.purpose,
                "booking_date": booking.booking_date.isoformat(),
                "start_time": booking.start_time.isoformat(),
                "end_time": booking.end_time.isoformat(),
                "duration_slots": booking.duration_slots,
                "status": booking.status.value,
                "notes": booking.notes,
                "created_at": booking.created_at.isoformat(),
                "updated_at": booking.updated_at.isoformat(),
                "approved_by_id": booking.approved_by_id,
                "approved_at": booking.approved_at.isoformat() if booking.approved_at else None
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving bookings: {str(e)}"
        )


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
    """Cancel a room booking and free up the slots"""
    
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
    
    # Mark slots as available
    mark_slots_as_available(
        db, booking.room_id, booking.booking_date,
        booking.start_time, booking.end_time
    )
    
    # Update booking status
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


# Utility Endpoints (Admin only)
@router.post("/admin/initialize-all-slots")
def initialize_all_room_slots(
    db: get_db,
    current_user: get_current_user
):
    """Initialize time slots for all rooms (Admin only)"""
    check_admin_role(current_user)
    
    slot_manager = SlotManager(db)
    result = slot_manager.initialize_all_room_slots()
    
    if result["success"]:
        return result
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )


@router.post("/admin/roll-daily-slots")
def admin_roll_daily_slots(
    db: get_db,
    current_user: get_current_user
):
    """Manually trigger daily slot rolling (Admin only)"""
    check_admin_role(current_user)
    
    slot_manager = SlotManager(db)
    result = slot_manager.roll_daily_slots()
    
    if result["success"]:
        return result
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )


@router.post("/admin/cleanup-expired-bookings")
def cleanup_expired_bookings(
    db: get_db,
    current_user: get_current_user
):
    """Clean up expired bookings and free their slots (Admin only)"""
    check_admin_role(current_user)
    
    slot_manager = SlotManager(db)
    result = slot_manager.cleanup_expired_bookings()
    
    if result["success"]:
        return result
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )


@router.get("/admin/slot-statistics")
def get_slot_statistics(
    db: get_db,
    current_user: get_current_user
):
    """Get detailed slot usage statistics (Admin only)"""
    check_admin_role(current_user)
    
    slot_manager = SlotManager(db)
    stats = slot_manager.get_slot_statistics()
    
    if "error" in stats:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=stats["error"]
        )
    
    return stats


@router.get("/admin/validate-slots")
def validate_slot_consistency(
    db: get_db,
    current_user: get_current_user
):
    """Validate slot data consistency (Admin only)"""
    check_admin_role(current_user)
    
    slot_manager = SlotManager(db)
    validation = slot_manager.validate_slot_consistency()
    
    if "error" in validation:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=validation["error"]
        )
    
    return validation


@router.get("/admin/system-status")
def get_system_status(
    db: get_db,
    current_user: get_current_user
):
    """Get system status and statistics (Admin only)"""
    check_admin_role(current_user)
    
    total_rooms = db.query(Room).count()
    available_rooms = db.query(Room).filter(Room.status == RoomStatus.AVAILABLE).count()
    
    today = date.today()
    today_bookings = db.query(RoomBooking).filter(
        and_(
            RoomBooking.booking_date == today,
            RoomBooking.status == RoomBookingStatus.SCHEDULED
        )
    ).count()
    
    # Get detailed statistics from SlotManager
    slot_manager = SlotManager(db)
    slot_stats = slot_manager.get_slot_statistics()
    
    system_status = {
        "total_rooms": total_rooms,
        "available_rooms": available_rooms,
        "today_bookings": today_bookings,
        "current_date": today.isoformat(),
        "system_time": datetime.now().isoformat()
    }
    
    # Merge slot statistics if available
    if "error" not in slot_stats:
        system_status.update(slot_stats)
    
    return system_status
