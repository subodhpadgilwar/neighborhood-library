from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class GenreStats(BaseModel):
    genre: str
    total_books: int
    total_copies: int
    available_copies: int
    percentage: float


class MonthlyLendingStats(BaseModel):
    month: str
    total_loans: int
    returned_loans: int
    overdue_loans: int
    active_loans: int


class TopBookStats(BaseModel):
    id: UUID
    title: str
    author: str
    genre: Optional[str] = None
    shelf_location: Optional[str] = None
    copies_total: int
    copies_available: int
    total_borrows: int
    current_borrows: int
    utilization_rate: float


class SummaryStatsResponse(BaseModel):
    total_books: int
    total_members: int
    active_loans: int
    overdue_loans: int
    total_copies: int
    available_copies: int
    loans_today: int
    returns_today: int
