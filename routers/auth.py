from fastapi import APIRouter, HTTPException, status
from dependency import get_db
from schemas import UserLogin, UserCreate
from models import User
from oauth2 import createAccessToken
import utils

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", status_code=status.HTTP_200_OK)
def login(user: UserLogin, db: get_db):
    db_user = db.query(User).filter(User.email == user.email).first()

    if db_user:
        if utils.verify(user.password, db_user.password):
            access_token = createAccessToken(
                {
                    "id": db_user.id,
                    "email": db_user.email,
                    "role": db_user.role.value  # Convert enum to string value
                }
            )

            return {
                "access_token": access_token, 
                "type": "Bearer",
                "email": db_user.email,
                "user_role": db_user.role.value,  # Convert enum to string value
                "user_id": db_user.id
            }
        

        
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate, db: get_db):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    new_user = User(
        email=user.email,
        username=user.username,
        password=utils.hash(user.password),
        role=user.role,
        phone=user.phone,
        gender=user.gender,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "email": new_user.email,
        "username": new_user.username,
        "role": new_user.role.value  
    }

