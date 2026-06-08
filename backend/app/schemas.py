from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    avatar: Optional[str] = None
    bio: Optional[str] = None


class UserResponse(UserBase):
    id: int
    avatar: str
    bio: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


class CornerBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=10)
    category: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    images: Optional[str] = ""
    tags: Optional[str] = ""
    difficulty: Optional[str] = "easy"


class CornerCreate(CornerBase):
    pass


class CornerUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    images: Optional[str] = None
    tags: Optional[str] = None
    difficulty: Optional[str] = None
    is_hidden: Optional[bool] = None


class CornerResponse(CornerBase):
    id: int
    author_id: int
    author: Optional[UserResponse] = None
    is_hidden: bool
    checkin_count: Optional[int] = 0
    created_at: datetime

    class Config:
        from_attributes = True


class CheckInBase(BaseModel):
    content: Optional[str] = ""
    images: Optional[str] = ""
    rating: Optional[int] = 5


class CheckInCreate(CheckInBase):
    corner_id: int


class CheckInResponse(CheckInBase):
    id: int
    user_id: int
    corner_id: int
    user: Optional[UserResponse] = None
    corner: Optional[CornerResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RouteBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = ""
    estimated_time: Optional[int] = 60
    distance: Optional[float] = 0.0


class RouteCreate(RouteBase):
    corner_ids: List[int] = []


class RouteResponse(RouteBase):
    id: int
    user_id: int
    user: Optional[UserResponse] = None
    corners: List[CornerResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class AchievementBase(BaseModel):
    name: str
    description: str
    icon: Optional[str] = "🏆"
    condition_type: str
    condition_value: int


class AchievementResponse(AchievementBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserAchievementResponse(BaseModel):
    id: int
    achievement: AchievementResponse
    unlocked_at: datetime

    class Config:
        from_attributes = True


class ShareBase(BaseModel):
    content_type: str
    content_id: int
    platform: Optional[str] = ""


class ShareCreate(ShareBase):
    pass


class ShareResponse(ShareBase):
    id: int
    user_id: int
    user: Optional[UserResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    total_corners: int
    total_checkins: int
    total_routes: int
    total_achievements: int
    total_shares: int
    checkin_corners: List[int] = []
