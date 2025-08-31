from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from models import User
from fastapi import Depends, HTTPException, APIRouter,status
from dependency import get_db
import utils, oauth2

router = APIRouter(
    tags=["token"]
    
)

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],db:get_db
) :
    
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.password is not None:
        if not utils.verify(form_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    accessToken = oauth2.createAccessToken(data = {"id":user.id, 
                                                    "email":user.email,
                                                    "role":user.role.value})
    
    jwt_token = {
        "access_token": accessToken,
        "token_type": "bearer"
        
    }

    return jwt_token
