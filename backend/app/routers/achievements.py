from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta
import json
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import aiofiles

from ..database import get_db
from ..models import Achievement, UserAchievement, User, CheckIn, Corner, Route, Share, CornerLike
from ..schemas import (
    AchievementResponse,
    UserAchievementProgress,
    AchievementUnlockResponse,
    UserAchievementStats,
    AchievementShareCardResponse,
    AchievementBase
)
from ..auth import get_current_user
from ..config import get_settings

router = APIRouter(prefix="/achievements", tags=["Achievements"])

settings = get_settings()

RARITY_CONFIG = {
    "common": {
        "name": "普通",
        "color": "#9CA3AF",
        "bg_color": "#F3F4F6",
        "percentage": 40,
        "points": 10,
        "effect": "none",
        "icon": "⚪"
    },
    "rare": {
        "name": "稀有",
        "color": "#22C55E",
        "bg_color": "#DCFCE7",
        "percentage": 30,
        "points": 25,
        "effect": "subtle",
        "icon": "🟢"
    },
    "epic": {
        "name": "史诗",
        "color": "#A855F7",
        "bg_color": "#F3E8FF",
        "percentage": 20,
        "points": 50,
        "effect": "particles",
        "icon": "🟣"
    },
    "legendary": {
        "name": "传说",
        "color": "#F97316",
        "bg_color": "#FFEDD5",
        "percentage": 8,
        "points": 100,
        "effect": "fullscreen",
        "icon": "🟠"
    },
    "mythic": {
        "name": "神话",
        "color": "#EF4444",
        "bg_color": "#FEE2E2",
        "percentage": 2,
        "points": 200,
        "effect": "special",
        "icon": "🔴"
    }
}

LEVEL_CONFIG = [
    {"level": "bronze", "name": "青铜探索者", "min_points": 0, "icon": "🥉"},
    {"level": "silver", "name": "白银探索者", "min_points": 100, "icon": "🥈"},
    {"level": "gold", "name": "黄金探索者", "min_points": 300, "icon": "🥇"},
    {"level": "diamond", "name": "钻石探索者", "min_points": 600, "icon": "💎"}
]

DEFAULT_ACHIEVEMENTS = [
    {"name": "初出茅庐", "description": "完成第一次打卡", "icon": "🌱", "rarity": "common", "condition_type": "checkins_total", "condition_value": 1},
    {"name": "探索新手", "description": "完成5次打卡", "icon": "👣", "rarity": "common", "condition_type": "checkins_total", "condition_value": 5},
    {"name": "探索达人", "description": "完成20次打卡", "icon": "🏃", "rarity": "rare", "condition_type": "checkins_total", "condition_value": 20},
    {"name": "探索大师", "description": "完成50次打卡", "icon": "🎖️", "rarity": "epic", "condition_type": "checkins_total", "condition_value": 50},
    {"name": "打卡狂魔", "description": "完成100次打卡", "icon": "🔥", "rarity": "legendary", "condition_type": "checkins_total", "condition_value": 100},
    {"name": "角落发现者", "description": "发布第一个角落", "icon": "🔍", "rarity": "common", "condition_type": "corners_total", "condition_value": 1},
    {"name": "角落收藏家", "description": "发布5个角落", "icon": "📚", "rarity": "rare", "condition_type": "corners_total", "condition_value": 5},
    {"name": "城市记录者", "description": "发布20个角落", "icon": "📝", "rarity": "epic", "condition_type": "corners_total", "condition_value": 20},
    {"name": "路线规划师", "description": "创建第一条路线", "icon": "🗺️", "rarity": "common", "condition_type": "routes_total", "condition_value": 1},
    {"name": "社交达人", "description": "分享10次", "icon": "📤", "rarity": "rare", "condition_type": "shares_total", "condition_value": 10},
    {"name": "坚持不懈", "description": "连续打卡7天", "icon": "📅", "rarity": "rare", "condition_type": "checkins_consecutive", "condition_value": 7},
    {"name": "月度冠军", "description": "连续打卡30天", "icon": "🏆", "rarity": "epic", "condition_type": "checkins_consecutive", "condition_value": 30},
    {"name": "夜行者", "description": "在凌晨2点-6点打卡", "icon": "🌙", "rarity": "epic", "condition_type": "checkins_time", "condition_value": 1, "condition_meta": '{"start_hour": 2, "end_hour": 6}'},
    {"name": "早起的鸟儿", "description": "在早上5点-8点打卡", "icon": "🌅", "rarity": "rare", "condition_type": "checkins_time", "condition_value": 1, "condition_meta": '{"start_hour": 5, "end_hour": 8}'},
    {"name": "美食探险家", "description": "打卡5个美食探店类角落", "icon": "🍜", "rarity": "rare", "condition_type": "checkins_category", "condition_value": 5, "condition_meta": '{"category": "美食探店"}'},
    {"name": "文艺青年", "description": "打卡5个文艺空间类角落", "icon": "📚", "rarity": "rare", "condition_type": "checkins_category", "condition_value": 5, "condition_meta": '{"category": "文艺空间"}'},
    {"name": "分类达人", "description": "打卡过所有6个分类", "icon": "🎯", "rarity": "epic", "condition_type": "checkins_categories_unique", "condition_value": 6},
    {"name": "万人迷", "description": "发布的角落累计获得100个赞", "icon": "❤️", "rarity": "legendary", "condition_type": "corners_likes_total", "condition_value": 100},
    {"name": "城市漫步者", "description": "在3个不同城市打卡", "icon": "🏙️", "rarity": "rare", "condition_type": "checkins_cities_unique", "condition_value": 3},
    {"name": "旅行家", "description": "在5个不同城市打卡", "icon": "✈️", "rarity": "epic", "condition_type": "checkins_cities_unique", "condition_value": 5},
    {"name": "世界公民", "description": "在10个不同城市打卡", "icon": "🌍", "rarity": "legendary", "condition_type": "checkins_cities_unique", "condition_value": 10},
    {"name": "全能探索者", "description": "解锁15个成就", "icon": "👑", "rarity": "mythic", "condition_type": "achievements_unlocked", "condition_value": 15},
    {"name": "点赞狂魔", "description": "给50个角落点赞", "icon": "👍", "rarity": "rare", "condition_type": "likes_given_total", "condition_value": 50},
    {"name": "质量至上", "description": "发布的角落平均评分达到4.5分", "icon": "⭐", "rarity": "epic", "condition_type": "corners_avg_rating", "condition_value": 4.5, "condition_meta": '{"min_corners": 5}'},
]


async def init_default_achievements(db: AsyncSession):
    result = await db.execute(select(func.count(Achievement.id)))
    count = result.scalar() or 0
    if count == 0:
        for ach_def in DEFAULT_ACHIEVEMENTS:
            rarity = ach_def.get("rarity", "common")
            points = RARITY_CONFIG[rarity]["points"]
            effect = RARITY_CONFIG[rarity]["effect"]
            
            achievement = Achievement(
                name=ach_def["name"],
                description=ach_def["description"],
                icon=ach_def["icon"],
                rarity=rarity,
                points=points,
                condition_type=ach_def["condition_type"],
                condition_value=ach_def["condition_value"],
                condition_meta=ach_def.get("condition_meta", "{}"),
                unlock_effect=effect
            )
            db.add(achievement)
        await db.commit()


async def calculate_global_unlock_rate(db: AsyncSession, achievement_id: int) -> float:
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0
    if total_users == 0:
        return 0.0
    
    unlocked_users_result = await db.execute(
        select(func.count(UserAchievement.id)).where(
            and_(
                UserAchievement.achievement_id == achievement_id,
                UserAchievement.is_unlocked == True
            )
        )
    )
    unlocked_users = unlocked_users_result.scalar() or 0
    return round((unlocked_users / total_users) * 100, 2)


async def get_user_achievement_progress(db: AsyncSession, user_id: int, achievement_id: int) -> Optional[UserAchievement]:
    result = await db.execute(
        select(UserAchievement).where(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id
            )
        )
    )
    return result.scalar_one_or_none()


async def calculate_progress(db: AsyncSession, user_id: int, achievement: Achievement) -> int:
    condition_type = achievement.condition_type
    condition_value = achievement.condition_value
    
    try:
        condition_meta = json.loads(achievement.condition_meta or "{}")
    except (json.JSONDecodeError, TypeError):
        condition_meta = {}
    
    if condition_type == "checkins_total":
        result = await db.execute(
            select(func.count(CheckIn.id)).where(CheckIn.user_id == user_id)
        )
        return result.scalar() or 0
    
    elif condition_type == "corners_total":
        result = await db.execute(
            select(func.count(Corner.id)).where(
                and_(
                    Corner.author_id == user_id,
                    Corner.is_hidden == False
                )
            )
        )
        return result.scalar() or 0
    
    elif condition_type == "routes_total":
        result = await db.execute(
            select(func.count(Route.id)).where(Route.user_id == user_id)
        )
        return result.scalar() or 0
    
    elif condition_type == "shares_total":
        result = await db.execute(
            select(func.count(Share.id)).where(Share.user_id == user_id)
        )
        return result.scalar() or 0
    
    elif condition_type == "likes_given_total":
        result = await db.execute(
            select(func.count(CornerLike.id)).where(CornerLike.user_id == user_id)
        )
        return result.scalar() or 0
    
    elif condition_type == "checkins_consecutive":
        result = await db.execute(
            select(CheckIn.created_at).where(
                CheckIn.user_id == user_id
            ).order_by(CheckIn.created_at.desc())
        )
        checkin_dates = [row[0].date() for row in result.all()]
        
        if not checkin_dates:
            return 0
        
        consecutive_days = 0
        current_date = datetime.now().date()
        
        for i in range(len(checkin_dates)):
            expected_date = current_date - timedelta(days=i)
            if expected_date in checkin_dates:
                consecutive_days += 1
            elif i == 0 and (current_date - checkin_dates[0]).days > 1:
                return 0
            else:
                break
        
        return consecutive_days
    
    elif condition_type == "checkins_time":
        start_hour = condition_meta.get("start_hour", 0)
        end_hour = condition_meta.get("end_hour", 24)
        
        result = await db.execute(
            select(func.count(CheckIn.id)).where(
                and_(
                    CheckIn.user_id == user_id,
                    func.strftime('%H', CheckIn.created_at) >= f"{start_hour:02d}",
                    func.strftime('%H', CheckIn.created_at) < f"{end_hour:02d}"
                )
            )
        )
        return result.scalar() or 0
    
    elif condition_type == "checkins_category":
        category = condition_meta.get("category", "")
        result = await db.execute(
            select(func.count(CheckIn.id)).where(
                and_(
                    CheckIn.user_id == user_id,
                    CheckIn.corner.has(Corner.category == category)
                )
            )
        )
        return result.scalar() or 0
    
    elif condition_type == "checkins_categories_unique":
        result = await db.execute(
            select(func.distinct(Corner.category)).select_from(CheckIn).join(
                Corner, CheckIn.corner_id == Corner.id
            ).where(CheckIn.user_id == user_id)
        )
        categories = [row[0] for row in result.all() if row[0]]
        return len(categories)
    
    elif condition_type == "checkins_cities_unique":
        result = await db.execute(
            select(func.distinct(Corner.city)).select_from(CheckIn).join(
                Corner, CheckIn.corner_id == Corner.id
            ).where(
                and_(
                    CheckIn.user_id == user_id,
                    Corner.city != ""
                )
            )
        )
        cities = [row[0] for row in result.all() if row[0]]
        return len(cities)
    
    elif condition_type == "corners_likes_total":
        result = await db.execute(
            select(func.sum(Corner.likes_count)).where(
                and_(
                    Corner.author_id == user_id,
                    Corner.is_hidden == False
                )
            )
        )
        return result.scalar() or 0
    
    elif condition_type == "corners_avg_rating":
        min_corners = condition_meta.get("min_corners", 1)
        result = await db.execute(
            select(Corner.id).where(
                and_(
                    Corner.author_id == user_id,
                    Corner.is_hidden == False
                )
            )
        )
        corner_ids = [row[0] for row in result.all()]
        
        if len(corner_ids) < min_corners:
            return 0
        
        if not corner_ids:
            return 0
        
        result = await db.execute(
            select(func.avg(CheckIn.rating)).where(
                CheckIn.corner_id.in_(corner_ids)
            )
        )
        avg_rating = result.scalar() or 0
        return int(avg_rating * 10) / 10
    
    elif condition_type == "achievements_unlocked":
        result = await db.execute(
            select(func.count(UserAchievement.id)).where(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.is_unlocked == True
                )
            )
        )
        return result.scalar() or 0
    
    return 0


async def check_and_unlock_achievements(user_id: int, db: AsyncSession) -> List[AchievementUnlockResponse]:
    await init_default_achievements(db)
    
    result = await db.execute(
        select(Achievement).where(Achievement.is_active == True)
    )
    achievements = result.scalars().all()
    
    unlocked_achievements = []
    
    for achievement in achievements:
        current_progress = await calculate_progress(db, user_id, achievement)
        user_ach = await get_user_achievement_progress(db, user_id, achievement.id)
        
        if not user_ach:
            user_ach = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
                progress=0,
                is_unlocked=False
            )
            db.add(user_ach)
            await db.flush()
        
        progress_changed = current_progress != user_ach.progress
        user_ach.progress = current_progress
        
        is_new_unlock = False
        if not user_ach.is_unlocked and current_progress >= achievement.condition_value:
            user_ach.is_unlocked = True
            user_ach.unlocked_at = datetime.now()
            is_new_unlock = True
        
        if progress_changed or is_new_unlock:
            await db.flush()
            
            global_rate = await calculate_global_unlock_rate(db, achievement.id)
            ach_response = AchievementResponse(
                id=achievement.id,
                name=achievement.name,
                description=achievement.description,
                icon=achievement.icon,
                rarity=achievement.rarity,
                points=achievement.points,
                condition_type=achievement.condition_type,
                condition_value=achievement.condition_value,
                condition_meta=achievement.condition_meta,
                is_active=achievement.is_active,
                unlock_effect=achievement.unlock_effect,
                global_unlock_rate=global_rate,
                created_at=achievement.created_at,
                updated_at=achievement.updated_at
            )
            
            progress_pct = min((current_progress / achievement.condition_value) * 100, 100) if achievement.condition_value > 0 else 100
            ua_response = UserAchievementProgress(
                id=user_ach.id,
                achievement=ach_response,
                progress=current_progress,
                is_unlocked=user_ach.is_unlocked,
                unlocked_at=user_ach.unlocked_at,
                progress_percentage=progress_pct,
                created_at=user_ach.created_at,
                updated_at=user_ach.updated_at
            )
            
            unlocked_achievements.append(AchievementUnlockResponse(
                success=True,
                achievement=ach_response,
                user_achievement=ua_response,
                is_new_unlock=is_new_unlock
            ))
    
    await db.commit()
    return unlocked_achievements


def calculate_user_level(total_points: int) -> dict:
    current_level = LEVEL_CONFIG[0]
    next_level = LEVEL_CONFIG[1] if len(LEVEL_CONFIG) > 1 else None
    
    for i, level in enumerate(LEVEL_CONFIG):
        if total_points >= level["min_points"]:
            current_level = level
            if i + 1 < len(LEVEL_CONFIG):
                next_level = LEVEL_CONFIG[i + 1]
            else:
                next_level = None
    
    if next_level:
        current_level_min = current_level["min_points"]
        next_level_min = next_level["min_points"]
        progress = ((total_points - current_level_min) / (next_level_min - current_level_min)) * 100
        next_points = next_level_min - total_points
    else:
        progress = 100
        next_points = 0
    
    return {
        "level": current_level["level"],
        "level_name": current_level["name"],
        "icon": current_level["icon"],
        "current_points": total_points,
        "next_level_points": next_points,
        "current_level_progress": min(progress, 100)
    }


async def get_user_achievement_stats(db: AsyncSession, user_id: int) -> UserAchievementStats:
    total_ach_result = await db.execute(
        select(func.count(Achievement.id)).where(Achievement.is_active == True)
    )
    total_achievements = total_ach_result.scalar() or 0
    
    user_ach_result = await db.execute(
        select(UserAchievement).options(selectinload(UserAchievement.achievement)).where(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.is_unlocked == True
            )
        )
    )
    user_achievements = user_ach_result.scalars().all()
    
    total_points = sum(ua.achievement.points for ua in user_achievements)
    unlocked_count = len(user_achievements)
    
    rarity_breakdown = {}
    for ua in user_achievements:
        rarity = ua.achievement.rarity
        rarity_breakdown[rarity] = rarity_breakdown.get(rarity, 0) + 1
    
    level_info = calculate_user_level(total_points)
    
    return UserAchievementStats(
        total_achievements=total_achievements,
        unlocked_count=unlocked_count,
        total_points=total_points,
        level=level_info["level"],
        level_name=level_info["level_name"],
        next_level_points=level_info["next_level_points"],
        current_level_progress=level_info["current_level_progress"],
        rarity_breakdown=rarity_breakdown
    )


def generate_gradient_color(start_color, end_color, width, height):
    base = Image.new('RGB', (width, height), start_color)
    top = Image.new('RGB', (width, height), end_color)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        for x in range(width):
            mask_data.append(int(255 * (y / height)))
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base


async def generate_share_card(
    achievement_name: str,
    achievement_icon: str,
    rarity: str,
    unlock_time: datetime,
    global_rate: float,
    username: str
) -> str:
    width, height = 800, 1000
    
    rarity_config = RARITY_CONFIG.get(rarity, RARITY_CONFIG["common"])
    
    gradient_colors = {
        "common": ("#F3F4F6", "#E5E7EB"),
        "rare": ("#DCFCE7", "#BBF7D0"),
        "epic": ("#F3E8FF", "#E9D5FF"),
        "legendary": ("#FFEDD5", "#FED7AA"),
        "mythic": ("#FEE2E2", "#FECACA")
    }
    
    start_color, end_color = gradient_colors.get(rarity, gradient_colors["common"])
    bg = generate_gradient_color(start_color, end_color, width, height)
    
    draw = ImageDraw.Draw(bg)
    
    card_width, card_height = 680, 880
    card_x, card_y = 60, 60
    radius = 30
    
    card_bg = Image.new('RGBA', (card_width, card_height), (255, 255, 255, 230))
    mask = Image.new('L', (card_width, card_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (card_width, card_height)], radius, fill=255)
    bg.paste(card_bg, (card_x, card_y), mask)
    
    icon_size = 160
    icon_y = card_y + 80
    
    icon_bg_size = icon_size + 40
    icon_bg = Image.new('RGBA', (icon_bg_size, icon_bg_size), (0, 0, 0, 0))
    icon_bg_draw = ImageDraw.Draw(icon_bg)
    icon_bg_draw.ellipse([(0, 0), (icon_bg_size, icon_bg_size)], fill=rarity_config["bg_color"])
    bg.paste(icon_bg, (width // 2 - icon_bg_size // 2, icon_y - 20), icon_bg)
    
    try:
        font_size = 100
        font = ImageFont.truetype("arial.ttf", font_size)
    except (IOError, OSError):
        font = ImageFont.load_default()
    
    icon_text_bbox = draw.textbbox((0, 0), achievement_icon, font=font)
    icon_text_width = icon_text_bbox[2] - icon_text_bbox[0]
    icon_text_height = icon_text_bbox[3] - icon_text_bbox[1]
    draw.text(
        (width // 2 - icon_text_width // 2, icon_y + (icon_size - icon_text_height) // 2),
        achievement_icon,
        font=font,
        fill=(0, 0, 0)
    )
    
    try:
        title_font = ImageFont.truetype("arial.ttf", 44)
        desc_font = ImageFont.truetype("arial.ttf", 28)
        small_font = ImageFont.truetype("arial.ttf", 22)
    except (IOError, OSError):
        title_font = ImageFont.load_default()
        desc_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    title_bbox = draw.textbbox((0, 0), achievement_name, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(
        (width // 2 - title_width // 2, icon_y + icon_size + 40),
        achievement_name,
        font=title_font,
        fill=(41, 37, 36)
    )
    
    rarity_text = f"{rarity_config['icon']} {rarity_config['name']}成就"
    rarity_bbox = draw.textbbox((0, 0), rarity_text, font=desc_font)
    rarity_width = rarity_bbox[2] - rarity_bbox[0]
    
    rarity_tag_x = width // 2 - rarity_width // 2 - 20
    rarity_tag_y = icon_y + icon_size + 105
    rarity_tag_width = rarity_width + 40
    rarity_tag_height = 50
    
    rarity_bg = Image.new('RGBA', (rarity_tag_width, rarity_tag_height), (0, 0, 0, 0))
    rarity_bg_draw = ImageDraw.Draw(rarity_bg)
    rarity_bg_draw.rounded_rectangle(
        [(0, 0), (rarity_tag_width, rarity_tag_height)],
        25,
        fill=rarity_config["color"]
    )
    bg.paste(rarity_bg, (rarity_tag_x, rarity_tag_y), rarity_bg)
    
    draw.text(
        (width // 2 - rarity_width // 2, rarity_tag_y + 10),
        rarity_text,
        font=desc_font,
        fill=(255, 255, 255)
    )
    
    divider_y = rarity_tag_y + rarity_tag_height + 40
    draw.line(
        [(card_x + 60, divider_y), (card_x + card_width - 60, divider_y)],
        fill=(229, 231, 235),
        width=2
    )
    
    info_y = divider_y + 40
    info_spacing = 70
    
    unlock_date_str = unlock_time.strftime("%Y年%m月%d日")
    info_items = [
        ("👤 获得者", username),
        ("📅 解锁时间", unlock_date_str),
        ("🌍 全球解锁率", f"{global_rate}%"),
        ("🏆 成就点数", f"+{rarity_config['points']} 点")
    ]
    
    for i, (label, value) in enumerate(info_items):
        item_y = info_y + i * info_spacing
        
        draw.text(
            (card_x + 80, item_y),
            label,
            font=small_font,
            fill=(120, 113, 108)
        )
        
        value_bbox = draw.textbbox((0, 0), str(value), font=desc_font)
        draw.text(
            (card_x + card_width - 80 - (value_bbox[2] - value_bbox[0]), item_y - 5),
            str(value),
            font=desc_font,
            fill=(41, 37, 36)
        )
    
    footer_y = card_y + card_height - 100
    app_name = "🌿 角落探索"
    app_bbox = draw.textbbox((0, 0), app_name, font=desc_font)
    app_width = app_bbox[2] - app_bbox[0]
    draw.text(
        (width // 2 - app_width // 2, footer_y),
        app_name,
        font=desc_font,
        fill=(34, 197, 94)
    )
    
    slogan = "发现城市里的每一处美好"
    slogan_bbox = draw.textbbox((0, 0), slogan, font=small_font)
    slogan_width = slogan_bbox[2] - slogan_bbox[0]
    draw.text(
        (width // 2 - slogan_width // 2, footer_y + 40),
        slogan,
        font=small_font,
        fill=(168, 162, 158)
    )
    
    os.makedirs(settings.STORAGE_LOCAL_PATH, exist_ok=True)
    filename = f"achievement_share_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}.png"
    filepath = os.path.join(settings.STORAGE_LOCAL_PATH, filename)
    
    async with aiofiles.open(filepath, 'wb') as f:
        buffer = BytesIO()
        bg.save(buffer, format='PNG')
        await f.write(buffer.getvalue())
    
    return f"{settings.STORAGE_BASE_URL}/{filename}"


@router.get("", response_model=List[AchievementResponse])
async def get_achievements(
    rarity: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    await init_default_achievements(db)
    
    query = select(Achievement).where(Achievement.is_active == True)
    if rarity:
        query = query.where(Achievement.rarity == rarity)
    
    result = await db.execute(query.order_by(Achievement.points))
    achievements = result.scalars().all()
    
    response = []
    for ach in achievements:
        global_rate = await calculate_global_unlock_rate(db, ach.id)
        response.append(AchievementResponse(
            id=ach.id,
            name=ach.name,
            description=ach.description,
            icon=ach.icon,
            rarity=ach.rarity,
            points=ach.points,
            condition_type=ach.condition_type,
            condition_value=ach.condition_value,
            condition_meta=ach.condition_meta,
            is_active=ach.is_active,
            unlock_effect=ach.unlock_effect,
            global_unlock_rate=global_rate,
            created_at=ach.created_at,
            updated_at=ach.updated_at
        ))
    
    return response


@router.get("/user", response_model=List[UserAchievementProgress])
async def get_user_achievements(
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_user_id = user_id if user_id else current_user.id
    await init_default_achievements(db)
    
    newly_unlocked = await check_and_unlock_achievements(target_user_id, db)
    
    result = await db.execute(
        select(UserAchievement).options(selectinload(UserAchievement.achievement)).where(
            UserAchievement.user_id == target_user_id
        ).order_by(UserAchievement.is_unlocked.desc(), UserAchievement.unlocked_at.desc())
    )
    user_achievements = result.scalars().all()
    
    all_ach_result = await db.execute(
        select(Achievement).where(Achievement.is_active == True)
    )
    all_achievements = all_ach_result.scalars().all()
    
    existing_ach_ids = {ua.achievement_id for ua in user_achievements}
    for ach in all_achievements:
        if ach.id not in existing_ach_ids:
            progress = await calculate_progress(db, target_user_id, ach)
            ua = UserAchievement(
                user_id=target_user_id,
                achievement_id=ach.id,
                progress=progress,
                is_unlocked=progress >= ach.condition_value
            )
            if ua.is_unlocked:
                ua.unlocked_at = datetime.now()
            db.add(ua)
            user_achievements.append(ua)
    
    await db.commit()
    
    response = []
    for ua in sorted(user_achievements, key=lambda x: (not x.is_unlocked, -(x.unlocked_at or datetime.min).timestamp())):
        global_rate = await calculate_global_unlock_rate(db, ua.achievement.id)
        ach_response = AchievementResponse(
            id=ua.achievement.id,
            name=ua.achievement.name,
            description=ua.achievement.description,
            icon=ua.achievement.icon,
            rarity=ua.achievement.rarity,
            points=ua.achievement.points,
            condition_type=ua.achievement.condition_type,
            condition_value=ua.achievement.condition_value,
            condition_meta=ua.achievement.condition_meta,
            is_active=ua.achievement.is_active,
            unlock_effect=ua.achievement.unlock_effect,
            global_unlock_rate=global_rate,
            created_at=ua.achievement.created_at,
            updated_at=ua.achievement.updated_at
        )
        
        progress_pct = min((ua.progress / ua.achievement.condition_value) * 100, 100) if ua.achievement.condition_value > 0 else 100
        response.append(UserAchievementProgress(
            id=ua.id,
            achievement=ach_response,
            progress=ua.progress,
            is_unlocked=ua.is_unlocked,
            unlocked_at=ua.unlocked_at,
            progress_percentage=progress_pct,
            created_at=ua.created_at,
            updated_at=ua.updated_at
        ))
    
    return response


@router.get("/user/stats", response_model=UserAchievementStats)
async def get_user_achievement_stats_endpoint(
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_user_id = user_id if user_id else current_user.id
    await init_default_achievements(db)
    return await get_user_achievement_stats(db, target_user_id)


@router.get("/check", response_model=List[AchievementUnlockResponse])
async def check_achievements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await check_and_unlock_achievements(current_user.id, db)


@router.get("/{achievement_id}/share", response_model=AchievementShareCardResponse)
async def generate_achievement_share_card(
    achievement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Achievement).where(Achievement.id == achievement_id)
    )
    achievement = result.scalar_one_or_none()
    
    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成就不存在"
        )
    
    user_ach_result = await db.execute(
        select(UserAchievement).where(
            and_(
                UserAchievement.user_id == current_user.id,
                UserAchievement.achievement_id == achievement_id,
                UserAchievement.is_unlocked == True
            )
        )
    )
    user_achievement = user_ach_result.scalar_one_or_none()
    
    if not user_achievement:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="你还未解锁此成就"
        )
    
    global_rate = await calculate_global_unlock_rate(db, achievement_id)
    
    image_url = await generate_share_card(
        achievement.name,
        achievement.icon,
        achievement.rarity,
        user_achievement.unlocked_at or datetime.now(),
        global_rate,
        current_user.username
    )
    
    return AchievementShareCardResponse(
        success=True,
        image_url=image_url,
        achievement_name=achievement.name,
        achievement_icon=achievement.icon,
        rarity=achievement.rarity,
        unlock_time=user_achievement.unlocked_at or datetime.now(),
        global_unlock_rate=global_rate
    )


@router.get("/rarity/config")
async def get_rarity_config():
    return RARITY_CONFIG


@router.get("/level/config")
async def get_level_config():
    return LEVEL_CONFIG
