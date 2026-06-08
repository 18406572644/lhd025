from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from ..database import get_db
from ..models import Route, RouteCorner, User, Corner
from ..schemas import RouteCreate, RouteResponse, CornerResponse
from ..auth import get_current_user

router = APIRouter(prefix="/routes", tags=["Routes"])


@router.get("", response_model=List[RouteResponse])
async def get_routes(
    skip: int = 0,
    limit: int = 20,
    user_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Route).options(selectinload(Route.user))

    if user_id:
        query = query.where(Route.user_id == user_id)

    query = query.order_by(Route.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    routes = result.scalars().all()

    response = []
    for route in routes:
        route_corners_result = await db.execute(
            select(RouteCorner).where(RouteCorner.route_id == route.id).order_by(RouteCorner.order)
        )
        route_corners = route_corners_result.scalars().all()

        corners = []
        for rc in route_corners:
            corner_result = await db.execute(
                select(Corner).where(Corner.id == rc.corner_id).options(selectinload(Corner.author))
            )
            corner = corner_result.scalar_one_or_none()
            if corner:
                corner_dict = corner.__dict__.copy()
                corner_dict['checkin_count'] = 0
                corner_dict['author'] = corner.author
                corners.append(CornerResponse(**corner_dict))

        route_dict = route.__dict__.copy()
        route_dict['corners'] = corners
        route_dict['user'] = route.user
        response.append(RouteResponse(**route_dict))

    return response


@router.get("/{route_id}", response_model=RouteResponse)
async def get_route(route_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Route).where(Route.id == route_id).options(selectinload(Route.user))
    )
    route = result.scalar_one_or_none()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    route_corners_result = await db.execute(
        select(RouteCorner).where(RouteCorner.route_id == route.id).order_by(RouteCorner.order)
    )
    route_corners = route_corners_result.scalars().all()

    corners = []
    for rc in route_corners:
        corner_result = await db.execute(
            select(Corner).where(Corner.id == rc.corner_id).options(selectinload(Corner.author))
        )
        corner = corner_result.scalar_one_or_none()
        if corner:
            corner_dict = corner.__dict__.copy()
            corner_dict['checkin_count'] = 0
            corner_dict['author'] = corner.author
            corners.append(CornerResponse(**corner_dict))

    route_dict = route.__dict__.copy()
    route_dict['corners'] = corners
    route_dict['user'] = route.user

    return RouteResponse(**route_dict)


@router.post("", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
async def create_route(
    route: RouteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_route = Route(
        title=route.title,
        description=route.description,
        estimated_time=route.estimated_time,
        distance=route.distance,
        user_id=current_user.id
    )

    db.add(db_route)
    await db.flush()

    for idx, corner_id in enumerate(route.corner_ids):
        corner_result = await db.execute(select(Corner).where(Corner.id == corner_id))
        corner = corner_result.scalar_one_or_none()
        if corner:
            db_route_corner = RouteCorner(
                route_id=db_route.id,
                corner_id=corner_id,
                order=idx
            )
            db.add(db_route_corner)

    await db.commit()
    await db.refresh(db_route)

    route_corners_result = await db.execute(
        select(RouteCorner).where(RouteCorner.route_id == db_route.id).order_by(RouteCorner.order)
    )
    route_corners = route_corners_result.scalars().all()

    corners = []
    for rc in route_corners:
        corner_result = await db.execute(
            select(Corner).where(Corner.id == rc.corner_id).options(selectinload(Corner.author))
        )
        corner = corner_result.scalar_one_or_none()
        if corner:
            corner_dict = corner.__dict__.copy()
            corner_dict['checkin_count'] = 0
            corner_dict['author'] = corner.author
            corners.append(CornerResponse(**corner_dict))

    route_dict = db_route.__dict__.copy()
    route_dict['corners'] = corners
    route_dict['user'] = current_user

    return RouteResponse(**route_dict)


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    route_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Route).where(Route.id == route_id))
    route = result.scalar_one_or_none()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    if route.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own routes"
        )

    route_corners_result = await db.execute(
        select(RouteCorner).where(RouteCorner.route_id == route.id)
    )
    route_corners = route_corners_result.scalars().all()
    for rc in route_corners:
        await db.delete(rc)

    await db.delete(route)
    await db.commit()

    return None
