from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

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

