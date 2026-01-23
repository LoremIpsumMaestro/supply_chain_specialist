"""Authentication endpoints for user registration and login."""

import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.db.base import get_db
from backend.models.user import (
    UserDB,
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
)
from backend.utils.auth import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    hash_password,
    verify_password,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user account.

    Creates a new user with hashed password and returns access and refresh tokens.
    """
    # Check if user already exists
    existing_user = db.query(UserDB).filter(UserDB.email == user_data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    try:
        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create new user
        new_user = UserDB(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=True,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Generate tokens
        access_token = create_access_token(new_user.id)
        refresh_token = create_refresh_token(new_user.id)

        logger.info(f"New user registered: {new_user.email}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(new_user),
        )

    except Exception as e:
        logger.error(f"Error registering user: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user account",
        )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # Rate limit: 5 attempts per minute
async def login(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Login with email and password.

    Returns access and refresh tokens if credentials are valid.
    Rate limited to 5 attempts per minute.
    """
    # Find user by email
    user = db.query(UserDB).filter(UserDB.email == credentials.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    logger.info(f"User logged in: {user.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using a valid refresh token.

    Returns a new access token and the same refresh token.
    """
    # Verify refresh token
    user_id = verify_refresh_token(refresh_request.refresh_token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Get user from database
    user = db.query(UserDB).filter(UserDB.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Generate new access token (keep the same refresh token)
    access_token = create_access_token(user.id)

    logger.info(f"Access token refreshed for user: {user.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_request.refresh_token,  # Return same refresh token
        user=UserResponse.model_validate(user),
    )


# Keep the demo token endpoint for backwards compatibility
@router.post("/demo-token")
async def get_demo_token() -> dict:
    """
    Get a demo token for testing purposes.

    For MVP, this creates a temporary user session without registration.
    In production, use /register and /login endpoints instead.
    """
    # Generate a demo user ID
    demo_user_id = uuid4()

    # Create JWT tokens
    access_token = create_access_token(demo_user_id)
    refresh_token = create_refresh_token(demo_user_id)

    logger.warning(f"Demo token generated for testing: {demo_user_id}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": str(demo_user_id),
        "message": "This is a demo token. Use /register or /login for production.",
    }
