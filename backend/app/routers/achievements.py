from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from typing import List

from ..database import get_db
from ..models import Achievement, UserAchievement, User, CheckIn, Corner, Route, Share
from ..schemas import AchievementResponse, UserAchievementResponse
from ..auth import get_current_user

router = APIRouter(prefix="/achievements", tags=["Achievements"])


async def check_and_unlock_achievements(user_id: int, db: AsyncSession):
    achievement_definitions = [
        {"name": "初出茅庐", "description": "完成第一次打卡", "icon": "🌱", "condition_type": "checkins", "condition_value": 1},
        {"name": "探索新手", "description": "完成5次打卡", "icon": "👣", "condition_type": "checkins", "condition_value": 5},
        {"name": "探索达人", "description": "完成20次打卡", "icon": "🏃", "condition_type": "checkins", "condition_value": 20},
        {"name": "探索大师", "description": "完成50次打卡", "icon": "🎖️", "condition_type": "checkins", "condition_value": 50},
        {"name": "角落发现者", "description": "发布第一个角落", "icon": "🔍", "condition_type": "corners", "condition_value": 1},
        {"name": "角落收藏家", "description": "发布5个角落", "icon": "📚", "condition_type": "corners", "condition_value": 5},
        {"name": "路线规划师", "description": "创建第一条路线", "icon": "🗺️", "condition_type": "routes", "condition_value": 1},
        {"name": "社交达人", "description": "分享10次", "icon": "📤", "condition_type": "shares", "condition_value": 10},
        {"name": "全能探索者", "description": "完成所有类型成就", "icon": "👑", "condition_type": "all", "condition_value": 100},
    ]

    checkins_result = await db.execute(
        select(func.count(CheckIn.id)).where(CheckIn.user_id == user_id)
    )
    checkins_count = checkins_result.scalar() or 0

    corners_result = await db.execute(
        select(func.count(Corner.id)).where(Corner.author_id == user_id, Corner.is_hidden == False)
    )
    corners_count = corners_result.scalar() or 0

    routes_result = await db.execute(
        select(func.count(Route.id)).where(Route.user_id == user_id)
    )
    routes_count = routes_result.scalar() or 0

    shares_result = await db.execute(
        select(func.count(Share.id)).where(Share.user_id == user_id)
    )
    shares_count = shares_result.scalar() or 0

    for ach_def in achievement_definitions:
        result = await db.execute(
            select(Achievement).where(Achievement.name == ach_def["name"])
        )
        achievement = result.scalar_one_or_none()

        if not achievement:
            achievement = Achievement(**ach_def)
            db.add(achievement)
            await db.flush()

        existing_ua_result = await db.execute(
            select(UserAchievement).where(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement.id
            )
        )
        if existing_ua_result.scalar_one_or_none():
            continue

        should_unlock = False
        if ach_def["condition_type"] == "checkins" and checkins_count >= ach_def["condition_value"]:
            should_unlock = True
        elif ach_def["condition_type"] == "corners" and corners_count >= ach_def["condition_value"]:
            should_unlock = True
        elif ach_def["condition_type"] == "routes" and routes_count >= ach_def["condition_value"]:
            should_unlock = True
        elif ach_def["condition_type"] == "shares" and shares_count >= ach_def["condition_value"]:
            should_unlock = True
        elif ach_def["condition_type"] == "all":
            total = checkins_count + corners_count + routes_count + shares_count
            if total >= ach_def["condition_value"]:
                should_unlock = True

        if should_unlock:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id
            )
            db.add(user_achievement)


@router.get("", response_model=List[AchievementResponse])
async def get_achievements(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Achievement))
    achievements = result.scalars().all()
    return achievements


@router.get("/user", response_model=List[UserAchievementResponse])
async def get_user_achievements(
    user_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_user_id = user_id if user_id else current_user.id
    await check_and_unlock_achievements(target_user_id, db)
    await db.commit()

    result = await db.execute(
        select(UserAchievement).where(UserAchievement.user_id == target_user_id).order_by(UserAchievement.unlocked_at.desc()).options(selectinload(UserAchievement.achievement))
    )
    user_achievements = result.scalars().all()

    return user_achievements
