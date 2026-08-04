from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.routers.deps import get_current_active_user
from backend.app.core.security import get_password_hash
from backend.app.core.exceptions import AlreadyExistsException
from backend.app.models.user import User
from backend.app.models.schemas import APIResponse, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=APIResponse[UserResponse],
    summary="Get current user profile"
)
def get_user_me(
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve profile details of currently authenticated user."""
    return APIResponse(
        data=UserResponse.model_validate(current_user)
    )


@router.put(
    "/me",
    response_model=APIResponse[UserResponse],
    summary="Update current user profile"
)
def update_user_me(
    update_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update profile information (email, username, password) of current user."""
    if update_in.email and update_in.email != current_user.email:
        if db.query(User).filter(User.email == update_in.email).first():
            raise AlreadyExistsException(message="Email is already taken")
        current_user.email = update_in.email
    
    if update_in.username and update_in.username != current_user.username:
        if db.query(User).filter(User.username == update_in.username).first():
            raise AlreadyExistsException(message="Username is already taken")
        current_user.username = update_in.username
    
    if update_in.password:
        current_user.hashed_password = get_password_hash(update_in.password)
    
    db.commit()
    db.refresh(current_user)

    return APIResponse(
        message="Profile updated successfully",
        data=UserResponse.model_validate(current_user)
    )
