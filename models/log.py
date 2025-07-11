from models import Base
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship

class SystemLog(Base):
    __tablename__ = 'system_logs'

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)  
    description = Column(Text, nullable=True)  
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  
    timestamp = Column(DateTime, nullable=False)  

    user = relationship("User")

    