from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

# Project internal imports
from app.core.security import create_access_token, verify_password, decode_token
from app.models.schemas import TokenResponse
from app.models.user import User
from app.core.database import get_db

# Logging setup - Debugging ki help avthundi
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# OAuth2 scheme setup - Swagger UI lo 'Authorize' button pani cheyalante idi kavali
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    """
    Bava, idi login endpoint. Username & Password check chesi JWT token isthundi.
    """
    print(f"--- DEBUG: Login attempt for user: {form_data.username} ---")

    try:
        # 1. Database nundi User ni vethuku
        result = await db.execute(select(User).where(User.username == form_data.username))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"--- DEBUG: User '{form_data.username}' not found in DB ---")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 2. Password verification (security.py lo bcrypt_sha256 vaadi verify chestundi)
        if not verify_password(form_data.password, user.hashed_password):
            print(f"--- DEBUG: Password mismatch for user: {form_data.username} ---")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. Token generate chesi return chey
        access_token = create_access_token(data={"sub": user.username})
        print(f"--- DEBUG: Token generated for {form_data.username} ---")
        
        return TokenResponse(access_token=access_token, token_type="bearer")

    except Exception as e:
        print(f"--- DEBUG CRASH: {str(e)} ---")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Bava, idi dependency function. Prathi protected route lo user identity ni idi check chestundi.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 1. Token decode chesi payload check chey
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
        
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
        
    # 2. Token lo unna username DB lo undo ledho check chey
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
        
    return user