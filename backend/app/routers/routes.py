from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from itertools import permutations
import math
from datetime import datetime, timezone

from ..database import get_db
from ..models import Route, RouteCorner, User, Corner, CheckIn
from ..schemas import RouteCreate, RouteResponse, CornerResponse, RouteRecommendRequest, RouteRecommendResponse
from ..auth import get_current_user
from .achievements import check_and_unlock_achievements

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

    await check_and_unlock_achievements(current_user.id, db)
    await db.commit()

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


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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


def nearest_neighbor_tsp(distance_matrix: List[List[float]], start: int = 0) -> List[int]:
    n = len(distance_matrix)
    if n == 0:
        return []
    if n == 1:
        return [0]
    
    unvisited = set(range(n))
    unvisited.remove(start)
    path = [start]
    current = start
    
    while unvisited:
        next_city = min(unvisited, key=lambda city: distance_matrix[current][city])
        path.append(next_city)
        unvisited.remove(next_city)
        current = next_city
    
    return path


def brute_force_tsp(distance_matrix: List[List[float]], start: int = 0) -> List[int]:
    n = len(distance_matrix)
    if n <= 3:
        return nearest_neighbor_tsp(distance_matrix, start)
    
    other_points = [i for i in range(n) if i != start]
    min_distance = float('inf')
    best_path = None
    
    max_permutations = 5000
    perm_count = 0
    for perm in permutations(other_points):
        perm_count += 1
        if perm_count > max_permutations:
            break
            
        path = [start] + list(perm)
        total = 0
        for i in range(len(path) - 1):
            total += distance_matrix[path[i]][path[i + 1]]
        
        if total < min_distance:
            min_distance = total
            best_path = path
    
    return best_path if best_path else nearest_neighbor_tsp(distance_matrix, start)


def solve_tsp(distance_matrix: List[List[float]], start: int = 0) -> List[int]:
    n = len(distance_matrix)
    if n <= 5:
        return brute_force_tsp(distance_matrix, start)
    else:
        return nearest_neighbor_tsp(distance_matrix, start)


def calculate_path_distance(distance_matrix: List[List[float]], path: List[int]) -> float:
    total = 0.0
    for i in range(len(path) - 1):
        total += distance_matrix[path[i]][path[i + 1]]
    return total


@router.post("/recommend", response_model=RouteRecommendResponse)
async def recommend_route(
    request: RouteRecommendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if request.start_corner_id is None and (request.start_lat is None or request.start_lng is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须指定起点：当前位置或指定角落"
        )

    if request.corner_count < 2 or request.corner_count > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角落数量必须在2到10之间"
        )

    query = select(Corner).where(Corner.is_hidden == False).options(selectinload(Corner.author))

    if request.category:
        query = query.where(Corner.category == request.category)
    if request.difficulty:
        query = query.where(Corner.difficulty == request.difficulty)

    result = await db.execute(query)
    all_corners = result.scalars().all()

    if len(all_corners) < request.corner_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"符合条件的角落不足，仅有 {len(all_corners)} 个可用角落"
        )

    start_lat, start_lng = None, None
    start_corner = None

    if request.start_corner_id is not None:
        start_corner_result = await db.execute(
            select(Corner).where(Corner.id == request.start_corner_id).options(selectinload(Corner.author))
        )
        start_corner = start_corner_result.scalar_one_or_none()
        if not start_corner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的起点角落不存在"
            )
        start_lat = start_corner.latitude
        start_lng = start_corner.longitude
    else:
        start_lat = request.start_lat
        start_lng = request.start_lng

    candidates = []
    for corner in all_corners:
        if start_corner and corner.id == start_corner.id:
            continue
        dist = haversine(start_lat, start_lng, corner.latitude, corner.longitude)
        candidates.append((dist, corner))

    candidates.sort(key=lambda x: x[0])
    selected_corners = [corner for _, corner in candidates[:request.corner_count - 1]]

    if start_corner:
        all_points = [start_corner] + selected_corners
    else:
        virtual_start = Corner(
            id=0,
            title="当前位置",
            description="这是您的当前位置，作为路线的起点开始探索",
            category="虚拟起点",
            latitude=start_lat,
            longitude=start_lng,
            is_hidden=False,
            author_id=current_user.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        virtual_start.author = current_user
        all_points = [virtual_start] + selected_corners

    n = len(all_points)
    distance_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                distance_matrix[i][j] = haversine(
                    all_points[i].latitude, all_points[i].longitude,
                    all_points[j].latitude, all_points[j].longitude
                )

    optimal_path = solve_tsp(distance_matrix, start=0)

    total_distance = calculate_path_distance(distance_matrix, optimal_path)
    estimated_time = int(total_distance * 15) + len(optimal_path) * 10

    ordered_corners = []
    for idx in optimal_path:
        corner = all_points[idx]
        checkin_result = await db.execute(
            select(func.count(CheckIn.id)).where(CheckIn.corner_id == corner.id)
        )
        checkin_count = checkin_result.scalar() or 0
        corner_dict = corner.__dict__.copy()
        corner_dict['checkin_count'] = checkin_count
        corner_dict['author'] = corner.author
        ordered_corners.append(CornerResponse(**corner_dict))

    segment_distances = []
    for i in range(len(optimal_path) - 1):
        segment_distances.append(round(distance_matrix[optimal_path[i]][optimal_path[i + 1]], 2))

    return RouteRecommendResponse(
        corners=ordered_corners,
        total_distance=round(total_distance, 2),
        estimated_time=estimated_time,
        order=optimal_path,
        distances=segment_distances
    )
