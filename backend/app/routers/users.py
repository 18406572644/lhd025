from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from ..database import get_db
from ..models import User, Corner, CheckIn, Route, Share, UserAchievement
from ..schemas import UserResponse, UserUpdate, UserStatsResponse
from ..auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    corners_result = await db.execute(
        select(func.count(Corner.id)).where(
            Corner.author_id == current_user.id,
            Corner.is_hidden == False
        )
    )
    total_corners = corners_result.scalar() or 0

    checkins_result = await db.execute(
        select(func.count(CheckIn.id)).where(CheckIn.user_id == current_user.id)
    )
    total_checkins = checkins_result.scalar() or 0

    routes_result = await db.execute(
        select(func.count(Route.id)).where(Route.user_id == current_user.id)
    )
    total_routes = routes_result.scalar() or 0

    achievements_result = await db.execute(
        select(func.count(UserAchievement.id)).where(UserAchievement.user_id == current_user.id)
    )
    total_achievements = achievements_result.scalar() or 0

    shares_result = await db.execute(
        select(func.count(Share.id)).where(Share.user_id == current_user.id)
    )
    total_shares = shares_result.scalar() or 0

    checkin_corners_result = await db.execute(
        select(CheckIn.corner_id).where(CheckIn.user_id == current_user.id)
    )
    checkin_corners = [row[0] for row in checkin_corners_result.all()]

    return UserStatsResponse(
        total_corners=total_corners,
        total_checkins=total_checkins,
        total_routes=total_routes,
        total_achievements=total_achievements,
        total_shares=total_shares,
        checkin_corners=checkin_corners
    )
