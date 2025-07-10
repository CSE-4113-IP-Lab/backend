from models import Base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now) 
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
 