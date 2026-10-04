from datetime import date, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, get_db


models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Library Management System")

FINE_PER_DAY = 5  # use this when calculating fines


# =====================================================
# BOOKS
# =====================================================

@app.post("/books", response_model=schemas.BookResponse, status_code=201)
def add_book(book: schemas.BookCreate, db: Session = Depends(get_db)):

    existing_book = db.query(models.Book).filter(
        models.Book.isbn == book.isbn
    ).first()

    if existing_book:
        raise HTTPException(
            status_code=400,
            detail="Book with this ISBN already exists"
        )

    new_book = models.Book(
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        category=book.category,
        total_copies=book.total_copies,
        available_copies=book.total_copies,
    )

    db.add(new_book)
    db.commit()
    db.refresh(new_book)

    return new_book


@app.get("/books", response_model=List[schemas.BookResponse])
def get_books(
    search: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):

    query = db.query(models.Book)

    if search:
        query = query.filter(
            (models.Book.title.ilike(f"%{search}%")) |
            (models.Book.author.ilike(f"%{search}%"))
        )

    if category:
        query = query.filter(models.Book.category == category)

    return query.all()


@app.get("/books/{book_id}", response_model=schemas.BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):

    book = db.query(models.Book).filter(
        models.Book.id == book_id
    ).first()

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    return book


@app.put("/books/{book_id}", response_model=schemas.BookResponse)
def update_book(
    book_id: int,
    data: schemas.BookUpdate,
    db: Session = Depends(get_db)
):

    book = db.query(models.Book).filter(
        models.Book.id == book_id
    ).first()

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(book, key, value)

    db.commit()
    db.refresh(book)

    return book


@app.delete("/books/{book_id}", response_model=schemas.MessageResponse)
def delete_book(book_id: int, db: Session = Depends(get_db)):

    book = db.query(models.Book).filter(
        models.Book.id == book_id
    ).first()

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    active_borrow = db.query(models.Borrow).filter(
        models.Borrow.book_id == book_id,
        models.Borrow.status == "borrowed"
    ).first()

    if active_borrow:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a book that is currently borrowed"
        )

    db.delete(book)
    db.commit()

    return {"message": "Book deleted successfully"}


# =====================================================
# MEMBERS
# =====================================================

@app.post("/members", response_model=schemas.MemberResponse, status_code=201)
def add_member(
    member: schemas.MemberCreate,
    db: Session = Depends(get_db)
):

    user = db.query(models.Member).filter(
        models.Member.email == member.email
    ).first()

    if user is None:

        new_member = models.Member(
            name=member.name,
            email=member.email,
            phone=member.phone
        )

        db.add(new_member)
        db.commit()
        db.refresh(new_member)

        return new_member

    raise HTTPException(
        status_code=400,
        detail="Email Already Exists"
    )


@app.get("/members", response_model=List[schemas.MemberResponse])
def get_members(
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):

    query = db.query(models.Member)

    if search:
        like = f"%{search}%"

        query = query.filter(
            (models.Member.name.ilike(like)) |
            (models.Member.email.ilike(like))
        )

    return query.all()


@app.get("/members/{member_id}", response_model=schemas.MemberResponse)
def get_member(
    member_id: int,
    db: Session = Depends(get_db)
):

    member = db.query(models.Member).filter(
        models.Member.id == member_id
    ).first()

    if member is None:
        raise HTTPException(
            status_code=404,
            detail="Member Not Found"
        )

    return member


@app.put("/members/{member_id}", response_model=schemas.MemberResponse)
def update_member(
    member_id: int,
    data: schemas.MemberUpdate,
    db: Session = Depends(get_db)
):

    user = db.query(models.Member).filter(
        models.Member.id == member_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Member Not Found"
        )

    updates = data.model_dump(exclude_unset=True)

    if "email" in updates and updates["email"] != user.email:

        taken = db.query(models.Member).filter(
            models.Member.email == updates["email"]
        ).first()

        if taken:
            raise HTTPException(
                status_code=400,
                detail="Email Already in Use"
            )

    for field, value in updates.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


@app.delete("/members/{member_id}", response_model=schemas.MessageResponse)
def delete_member(
    member_id: int,
    db: Session = Depends(get_db)
):

    member = db.query(models.Member).filter(
        models.Member.id == member_id
    ).first()

    if member is None:
        raise HTTPException(
            status_code=404,
            detail="Member Not Found"
        )

    active = db.query(models.Borrow).filter(
        models.Borrow.member_id == member_id,
        models.Borrow.status == "borrowed"
    ).first()

    if active:
        raise HTTPException(
            status_code=400,
            detail="Member has unreturned books, cannot delete"
        )

    db.query(models.Borrow).filter(
        models.Borrow.member_id == member_id
    ).delete()

    db.delete(member)
    db.commit()

    return {"message": "Member Deleted Successfully"}


@app.get(
    "/members/{member_id}/borrows",
    response_model=List[schemas.BorrowResponse]
)
def get_member_borrows(
    member_id: int,
    db: Session = Depends(get_db)
):

    member = db.query(models.Member).filter(
        models.Member.id == member_id
    ).first()

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member not found"
        )

    return db.query(models.Borrow).filter(
        models.Borrow.member_id == member_id
    ).all()


# =====================================================
# BORROW / RETURN
# =====================================================

@app.post(
    "/borrow",
    response_model=schemas.BorrowResponse,
    status_code=201
)
def borrow_book(
    data: schemas.BorrowCreate,
    db: Session = Depends(get_db)
):

    book = db.query(models.Book).filter(
        models.Book.id == data.book_id
    ).first()

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    member = db.query(models.Member).filter(
        models.Member.id == data.member_id
    ).first()

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member not found"
        )

    if not member.is_active:
        raise HTTPException(
            status_code=400,
            detail="Member is not active"
        )

    if book.available_copies <= 0:
        raise HTTPException(
            status_code=400,
            detail="No copies available"
        )

    already = db.query(models.Borrow).filter(
        models.Borrow.book_id == data.book_id,
        models.Borrow.member_id == data.member_id,
        models.Borrow.status == "borrowed"
    ).first()

    if already:
        raise HTTPException(
            status_code=400,
            detail="Member already has this book"
        )

    borrow = models.Borrow(
        book_id=data.book_id,
        member_id=data.member_id,
        borrow_date=date.today(),
        due_date=date.today() + timedelta(days=data.days),
        status="borrowed"
    )

    book.available_copies -= 1

    db.add(borrow)
    db.commit()
    db.refresh(borrow)

    return borrow


@app.post(
    "/return/{borrow_id}",
    response_model=schemas.BorrowResponse
)
def return_book(
    borrow_id: int,
    db: Session = Depends(get_db)
):

    borrow = db.query(models.Borrow).filter(
        models.Borrow.id == borrow_id
    ).first()

    if not borrow:
        raise HTTPException(
            status_code=404,
            detail="Borrow record not found"
        )

    if borrow.status == "returned":
        raise HTTPException(
            status_code=400,
            detail="Book has already been returned"
        )

    borrow.return_date = date.today()
    borrow.status = "returned"

    if borrow.return_date > borrow.due_date:

        late_days = (
            borrow.return_date - borrow.due_date
        ).days

        borrow.fine_amount = late_days * FINE_PER_DAY

    borrow.book.available_copies += 1

    db.commit()
    db.refresh(borrow)

    return borrow


@app.get(
    "/borrows",
    response_model=List[schemas.BorrowResponse]
)
def get_borrows(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):

    query = db.query(models.Borrow)

    if status:
        query = query.filter(
            models.Borrow.status == status
        )

    return query.all()


@app.get(
    "/borrows/overdue",
    response_model=List[schemas.BorrowResponse]
)
def get_overdue(db: Session = Depends(get_db)):

    overdue = db.query(models.Borrow).filter(
        models.Borrow.status == "borrowed",
        models.Borrow.due_date < date.today()
    ).all()

    return overdue


# =====================================================
# DASHBOARD
# =====================================================

@app.get("/stats", response_model=schemas.StatsResponse)
def get_stats(db: Session = Depends(get_db)):

    total_books = db.query(models.Book).count()

    total_members = db.query(models.Member).count()

    books_borrowed = db.query(models.Borrow).filter(
        models.Borrow.status == "borrowed"
    ).count()

    overdue_books = db.query(models.Borrow).filter(
        models.Borrow.status == "borrowed",
        models.Borrow.due_date < date.today()
    ).count()

    return {
        "total_books": total_books,
        "total_members": total_members,
        "books_borrowed": books_borrowed,
        "overdue_books": overdue_books
    }