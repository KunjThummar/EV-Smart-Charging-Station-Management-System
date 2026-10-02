from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(10), nullable=False, default="User")  # User / Admin
    created_at = Column(DateTime, default=datetime.now)

    bookings = relationship("Booking", back_populates="user")


class ChargingStation(Base):
    __tablename__ = "charging_stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    chargers = relationship("Charger", back_populates="station", cascade="all, delete")


class Charger(Base):
    __tablename__ = "chargers"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("charging_stations.id"), nullable=False)
    name = Column(String(50), nullable=False)
    charger_type = Column(String(10), nullable=False)  # Normal / Fast / Hyper
    status = Column(String(15), nullable=False, default="Available")  # Available / Occupied / Maintenance
    created_at = Column(DateTime, default=datetime.now)

    station = relationship("ChargingStation", back_populates="chargers")
    bookings = relationship("Booking", back_populates="charger")


class Pricing(Base):
    __tablename__ = "pricing"

    id = Column(Integer, primary_key=True, index=True)
    charger_type = Column(String(10), nullable=False, unique=True)
    price_per_hour = Column(Numeric(10, 2), nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


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
