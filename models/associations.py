from models import Base
from sqlalchemy import Column, ForeignKey, Table

# Association tables for many-to-many relationships
student_programs = Table(
    "student_programs",
    Base.metadata,
    Column("student_id", ForeignKey("students.id"), primary_key=True),
    Column("program_id", ForeignKey("programs.id"), primary_key=True)
)

faculty_programs = Table(
    "faculty_programs", 
    Base.metadata,
    Column("faculty_id", ForeignKey("faculties.id"), primary_key=True),
    Column("program_id", ForeignKey("programs.id"), primary_key=True)
)

post_files = Table(
    "post_files",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id"), primary_key=True),
    Column("file_id", ForeignKey("files.id"), primary_key=True)
)

coursework_files = Table(
    "coursework_files",
    Base.metadata,
    Column("coursework_id", ForeignKey("courseworks.id"), primary_key=True),
    Column("file_id", ForeignKey("files.id"), primary_key=True)
)

coursework_submission_files = Table(
    "coursework_submission_files",
    Base.metadata,
    Column("submission_id", ForeignKey("coursework_submissions.id"), primary_key=True),
    Column("file_id", ForeignKey("files.id"), primary_key=True)
)

post_participants = Table(
    "post_participants",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True)
)
