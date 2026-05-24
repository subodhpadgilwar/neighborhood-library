from fastapi import APIRouter

from app.api.v1 import analytics, auth, books, lending, members, staff

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(books.router)
api_router.include_router(members.router)
api_router.include_router(lending.router)
api_router.include_router(staff.router)
api_router.include_router(analytics.router)
