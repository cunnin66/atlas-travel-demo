import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from app.core.config import settings
from app.models.org import Org
from app.models.token import RefreshToken
from app.models.user import User
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt
from sqlalchemy.orm import Session

# Configure Argon2 with secure parameters for Argon2id
ph = PasswordHasher(
    time_cost=3,  # Number of iterations
    memory_cost=65536,  # Memory usage in KiB (64 MB)
    parallelism=1,  # Number of threads
    hash_len=32,  # Length of hash in bytes
    salt_len=16,  # Length of salt in bytes
    encoding="utf-8",
    type=Type.ID,  # Argon2id variant
)


# Load RSA keys for JWT
def _load_private_key() -> str:
    """Load RSA private key from environment variable"""
    # Replace literal \n with actual newlines if needed
    key = settings.JWT_PRIVATE_KEY.replace("\\n", "\n")
    return key


#     key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), settings.PRIVATE_KEY_PATH)
#     with open(key_path, 'r') as f:
#         return f.read()


def _load_public_key() -> str:
    """Load RSA public key from environment variable"""
    # Replace literal \n with actual newlines if needed
    key = settings.JWT_PUBLIC_KEY.replace("\\n", "\n")
    return key


#     key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), settings.PUBLIC_KEY_PATH)
#     with open(key_path, 'r') as f:
#         return f.read()


def clear_refresh_tokens(user: User, db: Session):
    """Clear all refresh tokens for a user"""
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update(
        {"is_revoked": True}
    )
    db.commit()


def create_access_token(user: User):
    """Create JWT access token using RS256"""

    to_encode = {"sub": user.id}
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire, "type": "access"})

    try:
        private_key = _load_private_key()
        encoded_jwt = jwt.encode(to_encode, private_key, algorithm=settings.ALGORITHM)
        return encoded_jwt
    except Exception as e:
        raise ValueError(f"Failed to create access token: {str(e)}")


def hash_jti(jti: str) -> str:
    """Hash JTI using SHA-256"""
    return hashlib.sha256(jti.encode()).hexdigest()


def create_refresh_token(user: User, db: Session):
    """Create JWT refresh token using RS256"""
    clear_refresh_tokens(user, db)

    to_encode = {"sub": user.id}
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti})

    try:
        private_key = _load_private_key()
        encoded_jwt = jwt.encode(to_encode, private_key, algorithm=settings.ALGORITHM)
        db.add(
            RefreshToken(hashed_jti=hash_jti(jti), user_id=user.id, expires_at=expire)
        )
        db.commit()
        return encoded_jwt
    except Exception as e:
        raise ValueError(f"Failed to create refresh token: {str(e)}")


def get_token_payload(token: str) -> Optional[dict]:
    """Verify and decode JWT token using RS256"""
    try:
        public_key = _load_public_key()
        payload = jwt.decode(token, public_key, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        # Token is invalid, expired, or malformed
        return None
    except Exception as e:
        # Other errors (file not found, etc.)
        return None


def is_access_token_valid(token: str) -> bool:
    """Check if access token is valid"""
    payload = get_token_payload(token)
    if not payload:
        return False
    return (
        payload["type"] == "access"
        and payload["sub"]
        and payload["exp"] > datetime.now(timezone.utc)
    )


def is_refresh_token_valid(token: str, db: Session) -> bool:
    """Check if refresh token is valid"""
    payload = get_token_payload(token)
    if not payload or not payload["jti"]:
        return False

    matching_record = (
        db.query(RefreshToken)
        .filter(RefreshToken.hashed_jti == hash_jti(payload["jti"]))
        .first()
    )
    return (
        matching_record
        and matching_record.expires_at > datetime.now(timezone.utc)
        and not matching_record.is_revoked
    )


def get_user_by_access_token(token: str, db: Session) -> Optional[User]:
    """Get user by token"""
    if not is_access_token_valid(token):
        return None

    payload = get_token_payload(token)
    return db.query(User).filter(User.id == payload["sub"]).first()


def hash_password(password: str) -> str:
    """Hash password using Argon2id"""
    try:
        return ph.hash(password)
    except Exception as e:
        raise ValueError(f"Failed to hash password: {str(e)}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against Argon2id hash"""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        # Password doesn't match
        return False
    except Exception as e:
        # Other errors (malformed hash, etc.)
        return False


def are_credentials_valid(username: str, password: str, db: Session) -> bool:
    """Check if login email and password are valid"""
    user = db.query(User).filter(User.email == username).first()
    if not user:
        return False
    return verify_password(password, user.hashed_password)


def is_email_available(email: str, db: Session) -> bool:
    """Check if email is available"""
    return db.query(User).filter(User.email == email).first() is None


def create_new_organization(name: str, db: Session) -> Org:
    """Create a new organization"""
    org = Org(name=name, slug=name.lower().replace(" ", "-"), description="")
    db.add(org)
    db.commit()
    return org


def create_new_user(email: str, password: str, org_id: int, db: Session) -> User:
    """Create a new user"""
    user = User(email=email, hashed_password=hash_password(password), org_id=org_id)
    db.add(user)
    db.commit()
    return user
