from datetime import date
from sqlalchemy import Column, Integer, String, Date, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    author = Column(String(100), nullable=False)
    isbn = Column(String(20), unique=True, nullable=False)
    category = Column(String(50))
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)

    borrows = relationship("Borrow", back_populates="book")


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(15))
    joined_date = Column(Date, default=date.today)
    is_active = Column(Boolean, default=True)

    borrows = relationship("Borrow", back_populates="member")


class Borrow(Base):
    __tablename__ = "borrows"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    borrow_date = Column(Date, default=date.today)
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)   # None = not returned yet
    fine_amount = Column(Float, default=0.0)
    status = Column(String(20), default="borrowed")  # "borrowed" or "returned"

    book = relationship("Book", back_populates="borrows")
    member = relationship("Member", back_populates="borrows")
