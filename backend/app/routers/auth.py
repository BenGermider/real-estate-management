from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas
from ..auth import verify_password, create_access_token, get_password_hash, get_current_user
from ..config import Settings
from ..db import get_session
from ..models import User

router = APIRouter(prefix="/auth", tags=["auth"])
settings = Settings()


@router.post("/login", response_model=schemas.Token)
async def login(request: schemas.LoginRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(seconds=settings.jwt_expires_seconds))
    return {"access_token": access_token, "token_type": "Bearer", "expires_in": settings.jwt_expires_seconds}


@router.get("/me", response_model=schemas.UserInfo)
async def me(current_user: User = Depends(get_current_user)):
    return {"user_id": str(current_user.id), "email": current_user.email, "roles": current_user.roles}

