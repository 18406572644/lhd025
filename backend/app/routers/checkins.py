from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from typing import List

from ..database import get_db
from ..models import CheckIn, User, Corner
from ..schemas import CheckInCreate, CheckInResponse
from ..auth import get_current_user
from .achievements import check_and_unlock_achievements

router = APIRouter(prefix="/checkins", tags=["Check-ins"])


@router.get("", response_model=List[CheckInResponse])
async def get_checkins(
    skip: int = 0,
    limit: int = 20,
    user_id: int = None,
    corner_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(CheckIn).options(selectinload(CheckIn.user), selectinload(CheckIn.corner).selectinload(Corner.author))

    if user_id is not None:
        query = query.where(CheckIn.user_id == user_id)
    if corner_id is not None:
        query = query.where(CheckIn.corner_id == corner_id)

    query = query.order_by(CheckIn.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    checkins = result.scalars().all()

    response = []
    for checkin in checkins:
        checkin_dict = checkin.__dict__.copy()
        
        if checkin.corner:
            checkin_result = await db.execute(
                select(func.count(CheckIn.id)).where(CheckIn.corner_id == checkin.corner.id)
            )
            checkin_count = checkin_result.scalar() or 0
            corner_dict = checkin.corner.__dict__.copy()
            corner_dict['checkin_count'] = checkin_count
            corner_dict['author'] = checkin.corner.author
            checkin_dict['corner'] = corner_dict
        
        response.append(CheckInResponse(**checkin_dict))

    return response


@router.get("/{checkin_id}", response_model=CheckInResponse)
async def get_checkin(checkin_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CheckIn).where(CheckIn.id == checkin_id).options(selectinload(CheckIn.user), selectinload(CheckIn.corner))
    )
    checkin = result.scalar_one_or_none()

    if not checkin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-in not found"
        )

    return checkin


@router.post("", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
async def create_checkin(
    checkin: CheckInCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Corner).where(Corner.id == checkin.corner_id))
    corner = result.scalar_one_or_none()

    if not corner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corner not found"
        )

    existing_result = await db.execute(
        select(CheckIn).where(
            CheckIn.user_id == current_user.id,
            CheckIn.corner_id == checkin.corner_id
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already checked in at this corner"
        )

    db_checkin = CheckIn(
        **checkin.model_dump(),
        user_id=current_user.id
    )

    db.add(db_checkin)
    await db.commit()
    await db.refresh(db_checkin)

    await check_and_unlock_achievements(current_user.id, db)
    await db.commit()

    result = await db.execute(
        select(CheckIn).where(CheckIn.id == db_checkin.id).options(selectinload(CheckIn.user), selectinload(CheckIn.corner))
    )
    db_checkin = result.scalar_one()

    return db_checkin


@router.delete("/{checkin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checkin(
    checkin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(CheckIn).where(CheckIn.id == checkin_id))
    checkin = result.scalar_one_or_none()

    if not checkin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-in not found"
        )

    if checkin.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own check-ins"
        )

    await db.delete(checkin)
    await db.commit()

    return None
