import enum

class MarkType(enum.Enum):
    INCOURSE = "incourse"
    FINAL = "final"
    OTHER = "other"

class MeetingStatusType(enum.Enum):
    SCHEDULED = "scheduled"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class InviteStatusType(enum.Enum):
    INVITED = "invited"
    ACCEPTED = "accepted"
    DECLINED = "declined"

class PostType(enum.Enum):
    NOTICE = "notice"
    ANNOUNCEMENT = "announcement"
    EVENT = "event"

class ScheduleType(enum.Enum):
    CLASS = "class"
    EXAM = "exam"
    SEMINAR = "seminar"

class DayOfWeek(enum.Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

class StatusType(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class EquipmentRequestStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    HANDOVER = "handover"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class SubmissionStatus(enum.Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    GRADED = "graded"
    LATE = "late"


class ProgramType(enum.Enum):
    BSc = "BSc"
    MSc = "MSc"
    PhD = "PhD"
    POSTDOC = "Postdoc"


class UserRole(enum.Enum):
    ADMIN = "admin"
    FACULTY = "faculty"
    STUDENT = "student"
    STAFF = "staff" 
    USER = "user"

class BookingType(enum.Enum):
    CLASSROOM = "classroom"
    LAB = "lab"
    CONFERENCE_ROOM = "conference_room"
    EVENT_SPACE = "event_space"

class RoomStatus(enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"


class RoomBookingStatus(enum.Enum):
    SCHEDULED = "scheduled"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OTPType(enum.Enum):
    Register ="REGISTER"
    FORGOT_PASSWORD = "FORGOT_PASSWORD"


class RoomStatus(enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"


class RoomBookingStatus(enum.Enum):
    SCHEDULED = "scheduled"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


