from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    charger_id = Column(Integer, ForeignKey("chargers.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    price_per_hour = Column(Numeric(10, 2), nullable=False)  # price at booking time
    total_cost = Column(Numeric(10, 2), nullable=False)
    status = Column(String(10), nullable=False, default="Booked")  # Booked / Cancelled
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="bookings")
    charger = relationship("Charger", back_populates="bookings")
