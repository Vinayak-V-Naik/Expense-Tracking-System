from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import db_helper

# JWT Configuration
SECRET_KEY = "your-secret-key-change-this-to-random-string-in-production-12345"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

security = HTTPBearer()

# Create router for auth endpoints
router = APIRouter()

# JWT Token Functions
def create_access_token(data: dict):
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user_id"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )
        return user_id
    except JWTError as e:
        print(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

# Pydantic Models

class UserSignup(BaseModel):
    actual_name: str
    username: str
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")

    @model_validator(mode="before")
    def check_password_strength(cls, values):
        password = values.get("password")
        if password:
            if not any(c.isupper() for c in password):
                raise ValueError("Password must contain at least one uppercase letter")
            if not any(c.islower() for c in password):
                raise ValueError("Password must contain at least one lowercase letter")
            if not any(c.isdigit() for c in password):
                raise ValueError("Password must contain at least one digit")
        return values


class UserLogin(BaseModel):
    username: str
    password: str

# Authentication Endpoints

@router.post('/signup')
def signup(request: UserSignup):
    try:
        existing_user = db_helper.get_user_by_username(request.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")

        db_helper.create_user(request.actual_name, request.username, request.password)
        print(f"User created: {request.username}")

        return {"message": "User created successfully"}
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error during signup: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


@router.post('/login')
def login(request: UserLogin):
    try:
        user = db_helper.get_user_by_username(request.username)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if not db_helper.verify_password(request.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        print(f"User logged in: {request.username}")

        # Create JWT access token
        access_token = create_access_token(data={"user_id": user['id']})

        return {
            "message": "Login successful",
            "user": {
                "id": user['id'],
                "name": user['actual_name'],
                "username": user['username']
            },
            "access_token": access_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during login: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")