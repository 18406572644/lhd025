from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from ..database import get_db
from ..models import Share, User
from ..schemas import ShareCreate, ShareResponse
from ..auth import get_current_user

router = APIRouter(prefix="/shares", tags=["Shares"])


@router.get("", response_model=List[ShareResponse])
async def get_shares(
    skip: int = 0,
    limit: int = 20,
    user_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Share)

    if user_id:
        query = query.where(Share.user_id == user_id)

    query = query.order_by(Share.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    shares = result.scalars().all()

    return shares


@router.post("", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
async def create_share(
    share: ShareCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_share = Share(
        **share.model_dump(),
        user_id=current_user.id
    )

    db.add(db_share)
    await db.commit()
    await db.refresh(db_share)

    return db_share
