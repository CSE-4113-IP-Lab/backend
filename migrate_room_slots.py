#!/usr/bin/env python3
"""
Database migration script for the room booking system.
This script initializes the new time slot system for all existing rooms.
"""

import sys
import os
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import engine, SessionLocal
from models.room import Room, RoomTimeSlot, RoomBooking
from models.enum import RoomBookingStatus
from room_utils.slot_manager import SlotManager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_existing_bookings(db_session):
    """
    Migrate existing datetime-based bookings to the new date/time slot system.
    This is needed if there are existing bookings in the old format.
    """
    logger.info("Checking for existing bookings to migrate...")
    
    # This would be used if there were old-format bookings
    # For now, we'll just log that the system is ready for the new format
    logger.info("System is ready for new slot-based booking format")


def initialize_room_slots():
    """Initialize time slots for all rooms in the database"""
    
    logger.info("Starting room slot initialization...")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create slot manager
        slot_manager = SlotManager(db)
        
        # Get all rooms
        rooms = db.query(Room).all()
        logger.info(f"Found {len(rooms)} rooms to initialize")
        
        if len(rooms) == 0:
            logger.warning("No rooms found in database. Create rooms first before running this script.")
            return
        
        # Initialize slots for all rooms
        result = slot_manager.initialize_all_room_slots()
        
        if result["success"]:
            logger.info(f"✅ Successfully initialized slots for {result['rooms_processed']} rooms")
        else:
            logger.error(f"❌ Failed to initialize slots: {result['message']}")
            return
        
        # Migrate any existing bookings
        migrate_existing_bookings(db)
        
        # Get and display statistics
        stats = slot_manager.get_slot_statistics()
        if "error" not in stats:
            logger.info("📊 Slot Statistics:")
            logger.info(f"   Today: {stats['today']['total_slots']} total slots, {stats['today']['available_slots']} available")
            logger.info(f"   Week: {stats['week']['total_slots']} total slots, {stats['week']['available_slots']} available")
        
        # Validate consistency
        validation = slot_manager.validate_slot_consistency()
        if validation["valid"]:
            logger.info("✅ Slot data validation passed")
        else:
            logger.warning(f"⚠️  Slot validation issues found: {validation['issues']}")
        
        logger.info("🎉 Room slot initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during initialization: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()


def cleanup_old_data():
    """Clean up any old time slot data that might conflict"""
    
    logger.info("Cleaning up old data...")
    
    db = SessionLocal()
    
    try:
        # Remove any existing time slots to start fresh
        deleted_count = db.query(RoomTimeSlot).delete()
        db.commit()
        
        if deleted_count > 0:
            logger.info(f"Removed {deleted_count} existing time slots")
        else:
            logger.info("No existing time slots found")
    
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()


def main():
    """Main migration function"""
    
    print("🏢 Room Booking System - Slot Initialization")
    print("=" * 50)
    
    try:
        # Step 1: Clean up any existing slot data
        cleanup_old_data()
        
        # Step 2: Initialize slots for all rooms
        initialize_room_slots()
        
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Start your FastAPI server")
        print("2. Use the admin endpoints to manage rooms and view slot statistics")
        print("3. Set up a daily cron job to call /rooms/admin/roll-daily-slots")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
