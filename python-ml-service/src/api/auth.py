"""
Authentication middleware for API security.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from pydantic import BaseModel

from ..utils.logger import get_logger

logger = get_logger(__name__)

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "hypergpu-dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

security = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    role: str = "user"


class AuthUser(BaseModel):
    user_id: str
    role: str


def create_access_token(user_id: str, role: str = "user") -> str:
    """Create a JWT access token."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire,
        "role": role
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[AuthUser]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return AuthUser(user_id=payload["sub"], role=payload.get("role", "user"))
    except jwt.ExpiredSignatureError:
        logger.warning("[Auth] Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"[Auth] Invalid token: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Optional[AuthUser]:
    """Get current authenticated user (optional)."""
    if credentials is None:
        return None
    
    user = verify_token(credentials.credentials)
    return user


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> AuthUser:
    """Require authentication."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = verify_token(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user


async def require_admin(user: AuthUser = Depends(require_auth)) -> AuthUser:
    """Require admin role."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
