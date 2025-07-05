from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Then import all models that use Base
from models.enum import *
from models.file import *
from models.associations import *
from models.user import *
from models.academic import *
from models.content import *
from models.resource import *
from models.administrative import *


