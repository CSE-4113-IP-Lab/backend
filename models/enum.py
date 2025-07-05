import enum

class MarkType(enum.Enum):
    MIDTERM = "midterm"
    FINAL = "final"
    ASSIGNMENT = "assignment"
    PROJECT = "project"

class MeetingStatusType(enum.Enum):
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

class StatusType(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    FAILED = "failed"

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


