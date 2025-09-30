from app.api.deps import get_current_admin_user, get_current_user, get_db
from app.core.security import (
    are_credentials_valid,
    create_access_token,
    create_new_organization,
    create_new_user,
    create_refresh_token,
    is_email_available,
)
from app.models.token import RefreshToken
from app.models.user import User, scrubUser
from app.schemas.token import Token, TokenRefresh
from app.schemas.user import UserCreate, UserInDB, UserRegister, UserResponse
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/register", response_model=Token)
async def register(form_data: UserRegister, db: Session = Depends(get_db)):
    """User register endpoint"""
    if not is_email_available(form_data.email, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    org = create_new_organization(form_data.org_name, db)

    user = create_new_user(form_data.email, form_data.password, org.id, db)
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user, db)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """User login endpoint"""
    if are_credentials_valid(form_data.username, form_data.password, db):
        user = db.query(User).filter(User.email == form_data.username).first()
        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user, db)
        return Token(access_token=access_token, refresh_token=refresh_token)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """Refresh access token"""
    # TODO: Implement token refresh
    pass


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """User logout endpoint"""
    token = current_user.refresh_tokens[-1].token
    db.query(RefreshToken).filter(RefreshToken.token == token).update(
        {"is_revoked": True}
    )
    db.commit()
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Validate token and return current user information"""
    return UserResponse(**scrubUser(current_user))


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create new user (Admin only)"""
    # TODO: Implement user creation
    pass
