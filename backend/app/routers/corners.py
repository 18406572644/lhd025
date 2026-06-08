from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from typing import List, Optional

from ..database import get_db
from ..models import Corner, User, CheckIn
from ..schemas import CornerCreate, CornerUpdate, CornerResponse
from ..auth import get_current_user

router = APIRouter(prefix="/corners", tags=["Corners"])


@router.get("", response_model=List[CornerResponse])
async def get_corners(
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Corner).where(Corner.is_hidden == False).options(selectinload(Corner.author))

    if category:
        query = query.where(Corner.category == category)
    if difficulty:
        query = query.where(Corner.difficulty == difficulty)
    if search:
        query = query.where(
            (Corner.title.contains(search)) |
            (Corner.description.contains(search)) |
            (Corner.tags.contains(search))
        )

    query = query.order_by(Corner.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    corners = result.scalars().all()

    response = []
    for corner in corners:
        checkin_result = await db.execute(
            select(func.count(CheckIn.id)).where(CheckIn.corner_id == corner.id)
        )
        checkin_count = checkin_result.scalar() or 0
        corner_dict = corner.__dict__.copy()
        corner_dict['checkin_count'] = checkin_count
        corner_dict['author'] = corner.author
        response.append(CornerResponse(**corner_dict))

    return response


@router.get("/{corner_id}", response_model=CornerResponse)
async def get_corner(corner_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Corner).where(Corner.id == corner_id).options(selectinload(Corner.author))
    )
    corner = result.scalar_one_or_none()

    if not corner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corner not found"
        )

    if corner.is_hidden:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This corner is hidden"
        )

    checkin_result = await db.execute(
        select(func.count(CheckIn.id)).where(CheckIn.corner_id == corner.id)
    )
    checkin_count = checkin_result.scalar() or 0

    corner_dict = corner.__dict__.copy()
    corner_dict['checkin_count'] = checkin_count
    corner_dict['author'] = corner.author

    return CornerResponse(**corner_dict)


@router.post("", response_model=CornerResponse, status_code=status.HTTP_201_CREATED)
async def create_corner(
    corner: CornerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_corner = Corner(
        **corner.model_dump(),
        author_id=current_user.id
    )

    db.add(db_corner)
    await db.commit()
    await db.refresh(db_corner)

    corner_dict = db_corner.__dict__.copy()
    corner_dict['checkin_count'] = 0
    corner_dict['author'] = current_user

    return CornerResponse(**corner_dict)


@router.put("/{corner_id}", response_model=CornerResponse)
async def update_corner(
    corner_id: int,
    corner_update: CornerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Corner).where(Corner.id == corner_id).options(selectinload(Corner.author))
    )
    db_corner = result.scalar_one_or_none()

    if not db_corner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corner not found"
        )

    if db_corner.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own corners"
        )

    update_data = corner_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_corner, field, value)

    await db.commit()
    await db.refresh(db_corner)

    checkin_result = await db.execute(
        select(func.count(CheckIn.id)).where(CheckIn.corner_id == db_corner.id)
    )
    checkin_count = checkin_result.scalar() or 0

    corner_dict = db_corner.__dict__.copy()
    corner_dict['checkin_count'] = checkin_count
    corner_dict['author'] = db_corner.author

    return CornerResponse(**corner_dict)


@router.delete("/{corner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_corner(
    corner_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Corner).where(Corner.id == corner_id))
    db_corner = result.scalar_one_or_none()

    if not db_corner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corner not found"
        )

    if db_corner.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own corners"
        )

    db_corner.is_hidden = True
    await db.commit()

    return None


@router.get("/nearby", response_model=List[CornerResponse])
async def get_nearby_corners(
    lat: float,
    lng: float,
    radius: float = 5.0,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Corner).where(Corner.is_hidden == False).options(selectinload(Corner.author))
    )
    all_corners = result.scalars().all()

    nearby_corners = []
    for corner in all_corners:
        distance = haversine(lat, lng, corner.latitude, corner.longitude)
        if distance <= radius:
            checkin_result = await db.execute(
                select(func.count(CheckIn.id)).where(CheckIn.corner_id == corner.id)
            )
            checkin_count = checkin_result.scalar() or 0
            corner_dict = corner.__dict__.copy()
            corner_dict['checkin_count'] = checkin_count
            corner_dict['author'] = corner.author
            corner_dict['distance'] = distance
            nearby_corners.append((distance, CornerResponse(**corner_dict)))

    nearby_corners.sort(key=lambda x: x[0])
    return [corner for _, corner in nearby_corners]


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    lon1_rad = math.radians(lon1)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
