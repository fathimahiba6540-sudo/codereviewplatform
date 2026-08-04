from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.core.security import decode_access_token
from backend.app.core.exceptions import CredentialsException, NotFoundException
from backend.app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Dependency verifying Bearer token and retrieving authenticated user."""
    user_id = decode_access_token(token)
    if not user_id:
        raise CredentialsException(message="Invalid or expired access token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException(message="User not found")
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency ensuring active account status."""
    if not current_user.is_active:
        raise CredentialsException(message="Inactive user account")
    return current_user
