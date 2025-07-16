from passlib.context import CryptContext
import logging
from fastapi import UploadFile, File as FileUpload
from sqlalchemy.orm import Session
from models import File, SystemLog
from datetime import datetime
import os
import uuid
import base64

pwdContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash(password:str):
    return pwdContext.hash(password)

def verify(plainPassword, hashedPassword):
    return pwdContext.verify(plainPassword, hashedPassword)


async def upload_file(db:Session, sub_dir:str, file:UploadFile=FileUpload(...)): 

    if not os.path.exists(f"media/{sub_dir}"):
        os.makedirs(f"media/{sub_dir}")

    try:
        file_extension = file.filename.split('.')[-1].lower()
        file_location = f"media/{sub_dir}/{uuid.uuid4()}_{file.filename}"
        file.file.seek(0)

        with open(file_location, "wb") as file_object:
            file_object.write(await file.read())

        file = File(url=file_location)
        db.add(file)
        db.commit()
        db.refresh(file)

        return file
    
    except Exception as e:
        logging.error(f"An error occurred while uploading the file: {e}")
        return None
    
def delete_file(db:Session, file_id:int):
    try:
        file = db.query(File).filter(File.id == file_id).first()
        if file:
            os.remove(file.url)
            db.delete(file)
            db.commit()
            return True
    except Exception as e:
        logging.error(f"An error occurred while deleting the file: {e}")
        return False
    

def encode_into_base64(file: UploadFile):
    try:
        # Reset file pointer to the beginning in case it has been read before
        file.file.seek(0)
        
        # Read and encode the file content
        encoded_content = base64.b64encode(file.file.read()).decode("utf-8")
        
        return encoded_content
    except Exception as e:
        logging.error(f"Failed to encode file into base64: {e}")
        return None


def decode_from_base64(base64_string:str):
    return base64.b64decode(base64_string)


def create_system_log(db: Session, action: str, user_id: int = None, details: str = None):
    try:
       
        
        log_entry = SystemLog(
            action=action,
            user_id=user_id,
            description=details,
            timestamp=datetime.now()
        )
        db.add(log_entry)
        db.commit()
        return log_entry
    except Exception as e:
        logging.error(f"Failed to create system log: {e}")
        return None

