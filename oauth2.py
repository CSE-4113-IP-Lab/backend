from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from db import get_db
from models.user import User
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

load_dotenv()

oauthScheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") 

def createAccessToken(data:dict):
    toEncode =data.copy()

    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    toEncode.update({"exp":expire})

    encodedJWT = jwt.encode(toEncode, SECRET_KEY, algorithm=ALGORITHM)
    return encodedJWT

def verifyAccessToken(Token: str, credentialException):

    try:
        payload = jwt.decode(Token, SECRET_KEY, algorithms=[ALGORITHM])
        id : str =  payload.get("id")
        if id is None:
            raise credentialException
    
    except JWTError:
        raise credentialException
    
    return id

def get_current_user(token : str= Depends(oauthScheme), db: Session = Depends(get_db)):
    credentialException = HTTPException(status_code=404, 
                                        detail="Token is invalid",
                                        headers={"WWW-Authenticate":"Bearer"})
    
    id = verifyAccessToken(token, credentialException)
    user = db.query(User).filter(User.id == id).first()
    return user