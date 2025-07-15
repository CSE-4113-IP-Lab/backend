from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta
from dependency import get_db
from schemas import UserLogin, UserCreate, OTPCreate, OTPVerify, OTPResponse, OAuthUserCreate
from models import User, Student, Faculty, UserRole, OTP, OTPType
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
    if user.role == UserRole.STUDENT:
        student = Student(
            user_id=new_user.id,
        )
    
        db.add(student)
    elif user.role == UserRole.FACULTY:
        faculty = Faculty(
            user_id=new_user.id,
        )
        db.add(faculty)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "email": new_user.email,
        "username": new_user.username,
        "role": new_user.role.value  
    }


@router.post("/saveOTP", response_model=OTPResponse, status_code=status.HTTP_201_CREATED)
def save_otp(otp_data: OTPCreate, db: get_db):
    """
    Save OTP for user verification (registration, password reset, etc.)
    """
   
    # Delete any existing OTP for this email and type
    db.query(OTP).filter(
        OTP.userEmail == otp_data.userEmail,
        OTP.type == otp_data.type
    ).delete()
    
    # Create new OTP
    new_otp = OTP(
        userEmail=otp_data.userEmail,
        otp=otp_data.otp,
        type=otp_data.type,
        created_at=datetime.now()
    )
    
    db.add(new_otp)
    db.commit()
    db.refresh(new_otp)
    
    return new_otp


@router.post("/verify", status_code=status.HTTP_200_OK)
def verify_otp(otp_verify: OTPVerify, db: get_db):
    """
    Verify OTP - checks if OTP is valid and within 3 minutes
    """
    # Find the OTP record
    otp_record = db.query(OTP).filter(
        OTP.userEmail == otp_verify.userEmail,
        OTP.type == otp_verify.type,
        OTP.otp == otp_verify.otp
    ).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid OTP or OTP not found"
        )
    
    # Check if OTP is within 3 minutes (180 seconds)
    current_time = datetime.now()
    time_diff = current_time - otp_record.created_at
    
    if time_diff.total_seconds() > 180:  # 3 minutes = 180 seconds
        # Delete expired OTP
        db.delete(otp_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="OTP has expired. Please request a new one."
        )
    
    # OTP is valid and within time limit
    # Delete the used OTP
    db.delete(otp_record)
    db.commit()
    
    # Get user information
    user = db.query(User).filter(User.email == otp_verify.userEmail).first()
    
    return {
        "detail": "OTP verified successfully",
    }


@router.post("/oauth", status_code=status.HTTP_200_OK)
def oauth_login(user: OAuthUserCreate, db: get_db):
    """
    OAuth login endpoint - creates user if doesn't exist or returns token for existing user
    """
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    
    if db_user:
        # User exists - return access token
        access_token = createAccessToken(
            {
                "id": db_user.id,
                "email": db_user.email,
                "role": db_user.role.value
            }
        )
        
        return {
            "access_token": access_token,
            "type": "Bearer",
            "email": db_user.email,
            "user_role": db_user.role.value,
            "user_id": db_user.id,
            "username": db_user.username,
            "is_new": False
        }
    
    else:
        # User doesn't exist - create new user
        new_user = User(
            email=user.email,
            username=user.username,
            password=None,  # OAuth users don't have passwords
            role=user.role,
            is_verified=1,  # OAuth users are considered verified
        )
        db.add(new_user)
        db.commit()
        
        # Create associated student or faculty record based on role
        if user.role == UserRole.STUDENT:
            student = Student(user_id=new_user.id)
            db.add(student)
        elif user.role == UserRole.FACULTY:
            faculty = Faculty(user_id=new_user.id)
            db.add(faculty)
        
        db.commit()
        db.refresh(new_user)
        
        # Generate access token for new user
        access_token = createAccessToken(
            {
                "id": new_user.id,
                "email": new_user.email,
                "role": new_user.role.value
            }
        )
        
        return {
            "access_token": access_token,
            "type": "Bearer",
            "email": new_user.email,
            "user_role": new_user.role.value,
            "user_id": new_user.id,
            "username": new_user.username,
            "is_new": True
        }

