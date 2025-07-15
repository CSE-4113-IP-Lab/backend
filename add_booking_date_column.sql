-- Migration SQL is not needed - booking_date column already exists in the model
-- The RoomBooking model already has: booking_date = Column(Date, nullable=False)

-- If you need to verify the column exists, you can run:
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'room_bookings';

-- For performance optimization, these indexes can be created if not exists:
CREATE INDEX IF NOT EXISTS idx_room_bookings_booking_date ON room_bookings(booking_date);
CREATE INDEX IF NOT EXISTS idx_room_bookings_status ON room_bookings(status);
CREATE INDEX IF NOT EXISTS idx_room_bookings_room_date ON room_bookings(room_id, booking_date);
