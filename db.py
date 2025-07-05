import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

sqlAlchemyDatabaseUrl = os.getenv("DB_URL")

engine = create_engine(sqlAlchemyDatabaseUrl)

SessionLocal = sessionmaker(autocommit =False, autoflush= False, bind= engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
