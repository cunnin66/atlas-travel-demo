from pydantic import BaseModel


class Token(BaseModel):
    """Token response schema"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token refresh request schema"""

    refresh_token: str


class TokenData(BaseModel):
    """Token data schema"""

    username: str
    user_id: int
    org_id: int
