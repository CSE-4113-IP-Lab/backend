"""
Utility functions for managing room time slots.
This module contains functions for slot initialization, daily rolling, and maintenance.
"""

from datetime import datetime, timedelta, time, date
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.room import Room, RoomTimeSlot, RoomBooking
from models.enum import RoomBookingStatus
import logging

logger = logging.getLogger(__name__)


class SlotManager:
    """Manager class for handling room time slot operations"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def initialize_all_room_slots(self) -> dict:
        """Initialize time slots for all rooms for the next 7 days"""
        try:
            rooms = self.db.query(Room).all()
            initialized_count = 0
            
            for room in rooms:
                self.generate_room_slots(room)
                initialized_count += 1
            
            logger.info(f"Successfully initialized slots for {initialized_count} rooms")
            return {
                "success": True,
                "message": f"Initialized slots for {initialized_count} rooms",
                "rooms_processed": initialized_count
            }
        
        except Exception as e:
            logger.error(f"Error initializing room slots: {str(e)}")
            self.db.rollback()
            return {
                "success": False,
                "message": f"Error initializing slots: {str(e)}",
                "rooms_processed": 0
            }
    
    def generate_room_slots(self, room: Room, start_date: date = None) -> None:
        """Generate 30-minute time slots for a room for the next 7 days"""
        if start_date is None:
            start_date = date.today()
        
        logger.info(f"Generating slots for room {room.room_number}")
        
        for day_offset in range(7):
            slot_date = start_date + timedelta(days=day_offset)
            
            # Clear existing slots for this date to avoid duplicates
            self.db.query(RoomTimeSlot).filter(
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
                self.db.add(slot)
                
                # Move to next 30-minute slot
                current_datetime = datetime.combine(slot_date, current_time)
                next_datetime = current_datetime + timedelta(minutes=30)
                current_time = next_datetime.time()
        
        self.db.commit()
    
    def roll_daily_slots(self) -> dict:
        """
        Roll slots forward daily:
        - Remove yesterday's slots
        - Add new day 7 slots
        - Update day_offset for remaining slots
        """
        try:
            today = date.today()
            yesterday = today - timedelta(days=1)
            day_7 = today + timedelta(days=6)
            
            logger.info(f"Rolling daily slots - removing {yesterday}, adding {day_7}")
            
            # Remove yesterday's slots
            deleted_count = self.db.query(RoomTimeSlot).filter(
                RoomTimeSlot.slot_date == yesterday
            ).delete()
            
            logger.info(f"Deleted {deleted_count} slots from {yesterday}")
            
            # Get all rooms and generate slots for day 7
            rooms = self.db.query(Room).all()
            new_slots_count = 0
            
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
                    self.db.add(slot)
                    new_slots_count += 1
                    
                    # Move to next 30-minute slot
                    current_datetime = datetime.combine(day_7, current_time)
                    next_datetime = current_datetime + timedelta(minutes=30)
                    current_time = next_datetime.time()
            
            # Update day_offset for remaining slots (shift all back by 1)
            remaining_slots = self.db.query(RoomTimeSlot).filter(
                RoomTimeSlot.slot_date >= today
            ).all()
            
            for slot in remaining_slots:
                slot.day_offset = (slot.slot_date - today).days
            
            self.db.commit()
            
            logger.info(f"Successfully rolled daily slots - added {new_slots_count} new slots")
            return {
                "success": True,
                "message": "Daily slot rolling completed successfully",
                "deleted_slots": deleted_count,
                "new_slots": new_slots_count
            }
        
        except Exception as e:
            logger.error(f"Error rolling daily slots: {str(e)}")
            self.db.rollback()
            return {
                "success": False,
                "message": f"Error rolling daily slots: {str(e)}",
                "deleted_slots": 0,
                "new_slots": 0
            }
    
    def cleanup_expired_bookings(self) -> dict:
        """Clean up expired bookings and free their slots"""
        try:
            today = date.today()
            current_time = datetime.now().time()
            
            # Find bookings that have ended
            expired_bookings = self.db.query(RoomBooking).filter(
                and_(
                    RoomBooking.booking_date < today,
                    RoomBooking.status.in_([RoomBookingStatus.SCHEDULED, RoomBookingStatus.ONGOING])
                )
            ).all()
            
            # Also find today's bookings that have ended
            today_expired = self.db.query(RoomBooking).filter(
                and_(
                    RoomBooking.booking_date == today,
                    RoomBooking.end_time < current_time,
                    RoomBooking.status.in_([RoomBookingStatus.SCHEDULED, RoomBookingStatus.ONGOING])
                )
            ).all()
            
            expired_bookings.extend(today_expired)
            
            cleaned_count = 0
            for booking in expired_bookings:
                # Mark booking as completed
                booking.status = RoomBookingStatus.COMPLETED
                
                # Free up the slots if they still exist
                slots = self.db.query(RoomTimeSlot).filter(
                    and_(
                        RoomTimeSlot.room_id == booking.room_id,
                        RoomTimeSlot.slot_date == booking.booking_date,
                        RoomTimeSlot.booking_id == booking.id
                    )
                ).all()
                
                for slot in slots:
                    slot.is_available = True
                    slot.booking_id = None
                
                cleaned_count += 1
            
            self.db.commit()
            
            logger.info(f"Cleaned up {cleaned_count} expired bookings")
            return {
                "success": True,
                "message": f"Cleaned up {cleaned_count} expired bookings",
                "cleaned_bookings": cleaned_count
            }
        
        except Exception as e:
            logger.error(f"Error cleaning up expired bookings: {str(e)}")
            self.db.rollback()
            return {
                "success": False,
                "message": f"Error cleaning up bookings: {str(e)}",
                "cleaned_bookings": 0
            }
    
    def get_slot_statistics(self) -> dict:
        """Get statistics about slot usage"""
        try:
            today = date.today()
            
            # Total slots today
            total_slots_today = self.db.query(RoomTimeSlot).filter(
                RoomTimeSlot.slot_date == today
            ).count()
            
            # Booked slots today
            booked_slots_today = self.db.query(RoomTimeSlot).filter(
                and_(
                    RoomTimeSlot.slot_date == today,
                    RoomTimeSlot.is_available == False
                )
            ).count()
            
            # Total slots in 7-day window
            end_date = today + timedelta(days=6)
            total_slots_week = self.db.query(RoomTimeSlot).filter(
                and_(
                    RoomTimeSlot.slot_date >= today,
                    RoomTimeSlot.slot_date <= end_date
                )
            ).count()
            
            # Booked slots in 7-day window
            booked_slots_week = self.db.query(RoomTimeSlot).filter(
                and_(
                    RoomTimeSlot.slot_date >= today,
                    RoomTimeSlot.slot_date <= end_date,
                    RoomTimeSlot.is_available == False
                )
            ).count()
            
            # Active bookings
            active_bookings = self.db.query(RoomBooking).filter(
                and_(
                    RoomBooking.booking_date >= today,
                    RoomBooking.status == RoomBookingStatus.SCHEDULED
                )
            ).count()
            
            return {
                "today": {
                    "total_slots": total_slots_today,
                    "booked_slots": booked_slots_today,
                    "available_slots": total_slots_today - booked_slots_today,
                    "utilization_percent": round((booked_slots_today / total_slots_today) * 100, 2) if total_slots_today > 0 else 0
                },
                "week": {
                    "total_slots": total_slots_week,
                    "booked_slots": booked_slots_week,
                    "available_slots": total_slots_week - booked_slots_week,
                    "utilization_percent": round((booked_slots_week / total_slots_week) * 100, 2) if total_slots_week > 0 else 0
                },
                "active_bookings": active_bookings
            }
        
        except Exception as e:
            logger.error(f"Error getting slot statistics: {str(e)}")
            return {
                "error": f"Error getting statistics: {str(e)}"
            }
    
    def validate_slot_consistency(self) -> dict:
        """Validate that slot data is consistent and report any issues"""
        try:
            issues = []
            
            # Check for slots without valid rooms
            orphaned_slots = self.db.query(RoomTimeSlot).filter(
                ~RoomTimeSlot.room_id.in_(
                    self.db.query(Room.id)
                )
            ).count()
            
            if orphaned_slots > 0:
                issues.append(f"{orphaned_slots} slots reference non-existent rooms")
            
            # Check for slots with invalid booking references
            invalid_booking_refs = self.db.query(RoomTimeSlot).filter(
                and_(
                    RoomTimeSlot.booking_id.isnot(None),
                    ~RoomTimeSlot.booking_id.in_(
                        self.db.query(RoomBooking.id)
                    )
                )
            ).count()
            
            if invalid_booking_refs > 0:
                issues.append(f"{invalid_booking_refs} slots reference non-existent bookings")
            
            # Check for bookings without corresponding slots
            today = date.today()
            end_date = today + timedelta(days=6)
            
            bookings_without_slots = self.db.query(RoomBooking).filter(
                and_(
                    RoomBooking.booking_date >= today,
                    RoomBooking.booking_date <= end_date,
                    RoomBooking.status == RoomBookingStatus.SCHEDULED,
                    ~RoomBooking.id.in_(
                        self.db.query(RoomTimeSlot.booking_id).filter(
                            RoomTimeSlot.booking_id.isnot(None)
                        )
                    )
                )
            ).count()
            
            if bookings_without_slots > 0:
                issues.append(f"{bookings_without_slots} bookings don't have corresponding slots marked")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "orphaned_slots": orphaned_slots,
                "invalid_booking_refs": invalid_booking_refs,
                "bookings_without_slots": bookings_without_slots
            }
        
        except Exception as e:
            logger.error(f"Error validating slot consistency: {str(e)}")
            return {
                "valid": False,
                "error": f"Error during validation: {str(e)}"
            }


def create_slot_manager(db_session: Session) -> SlotManager:
    """Factory function to create a SlotManager instance"""
    return SlotManager(db_session)
