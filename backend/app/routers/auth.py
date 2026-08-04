from datetime import timedelta
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.core.config import settings
from backend.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)
from backend.app.core.exceptions import (
    AppException,
    AlreadyExistsException,
    CredentialsException,
    NotFoundException
)
from backend.app.models.user import User
from backend.app.models.schemas import (
    APIResponse,
    UserCreate,
    UserResponse,
    Token,
    PasswordResetRequest,
    PasswordResetConfirm
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user account with hashed password."""
    # Check duplicate email
    if db.query(User).filter(User.email == user_in.email).first():
        raise AlreadyExistsException(message="User with this email already exists")
    
    # Check duplicate username
    if db.query(User).filter(User.username == user_in.username).first():
        raise AlreadyExistsException(message="User with this username already exists")
    
    # Create user
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return APIResponse(
        message="User registered successfully",
        data=UserResponse.model_validate(db_user)
    )


@router.post(
    "/login",
    response_model=Token,
    summary="User authentication login endpoint"
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user with username/email and password, returning JWT token."""
    # Query by username or email
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise CredentialsException(message="Incorrect username/email or password")
    
    if not user.is_active:
        raise CredentialsException(message="Account is inactive")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )

    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post(
    "/forgot-password",
    response_model=APIResponse[dict],
    summary="Request password reset token"
)
def forgot_password(
    request_in: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Generate a password reset token for the specified email."""
    user = db.query(User).filter(User.email == request_in.email).first()
    if not user:
        # Avoid user enumeration by returning standard success message
        return APIResponse(
            message="If the email is registered, a password reset token will be sent."
        )
    
    # Create short-lived reset token (15 mins)
    reset_token = create_access_token(
        subject=f"reset:{user.id}",
        expires_delta=timedelta(minutes=15)
    )

    return APIResponse(
        message="Password reset token generated",
        data={"reset_token": reset_token}
    )


@router.post(
    "/reset-password",
    response_model=APIResponse[dict],
    summary="Confirm password reset with token"
)
def reset_password(
    confirm_in: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset user password using token."""
    token_sub = decode_access_token(confirm_in.token)
    if not token_sub or not token_sub.startswith("reset:"):
        raise CredentialsException(message="Invalid or expired reset token")
    
    user_id = token_sub.replace("reset:", "")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException(message="User not found")
    
    user.hashed_password = get_password_hash(confirm_in.new_password)
    db.commit()

    return APIResponse(message="Password reset successfully")
