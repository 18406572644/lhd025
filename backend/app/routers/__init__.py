from .auth import router as auth_router
from .corners import router as corners_router
from .checkins import router as checkins_router
from .routes import router as routes_router
from .achievements import router as achievements_router
from .shares import router as shares_router
from .users import router as users_router
from .uploads import router as uploads_router

__all__ = [
    "auth_router",
    "corners_router",
    "checkins_router",
    "routes_router",
    "achievements_router",
    "shares_router",
    "users_router",
    "uploads_router",
]
