from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True


class UserRegister(BaseModel):
    """User registration schema"""

    email: EmailStr
    password: str
    org_name: str


class UserCreate(UserBase):
    """User creation schema"""

    password: str
    org_id: int


class UserUpdate(BaseModel):
    """User update schema"""

    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """User in database schema"""

    id: int
    hashed_password: str
    is_admin: bool
    org_id: int

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """User response schema"""

    id: int
    is_admin: bool
    org_id: int

    class Config:
        from_attributes = True
