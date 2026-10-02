from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Pricing(Base):
    __tablename__ = "pricing"

    id = Column(Integer, primary_key=True, index=True)
    charger_type = Column(String(10), nullable=False, unique=True)
    price_per_hour = Column(Numeric(10, 2), nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
