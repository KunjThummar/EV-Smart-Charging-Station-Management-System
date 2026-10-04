from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ---------- BOOK ----------
class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=100)
    isbn: str = Field(..., min_length=5, max_length=20)
    category: Optional[str] = None
    total_copies: int = Field(1, ge=1)


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    total_copies: Optional[int] = Field(None, ge=1)


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    isbn: str
    category: Optional[str]
    total_copies: int
    available_copies: int


# ---------- MEMBER ----------
class MemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    phone: Optional[str]
    joined_date: date
    is_active: bool


# ---------- BORROW ----------
class BorrowCreate(BaseModel):
    book_id: int
    member_id: int
    days: int = Field(14, ge=1, le=60)  # how many days the book is borrowed for


class BorrowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    member_id: int
    borrow_date: date
    due_date: date
    return_date: Optional[date]
    fine_amount: float
    status: str


# ---------- STATS ----------
class StatsResponse(BaseModel):
    total_books: int
    total_members: int
    books_borrowed: int
    overdue_books: int


# ---------- GENERIC ----------
class MessageResponse(BaseModel):
    message: str
