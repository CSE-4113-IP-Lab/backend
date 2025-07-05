from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, func, Enum, DateTime, Date, Time, Float, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()

# Then import all models that use Base
from models.file import *
from models.associations import *
from models.user import *
from models.academic import *
from models.content import *
from models.resource import *
from models.administrative import *
from models.enum import *

