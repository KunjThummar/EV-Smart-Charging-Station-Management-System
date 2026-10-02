from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict

ChargerType = Literal["Normal", "Fast", "Hyper"]
ChargerStatus = Literal["Available", "Occupied", "Maintenance"]


class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth / User ----------
class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    name: str


class UserOut(OrmBase):
    id: int
    name: str
    email: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


# ---------- Chargers ----------
class ChargerCreate(BaseModel):
    station_id: int
    name: str
    charger_type: ChargerType


class ChargerUpdate(BaseModel):
    name: str | None = None
    charger_type: ChargerType | None = None


class ChargerStatusUpdate(BaseModel):
    status: ChargerStatus


class ChargerOut(OrmBase):
    id: int
    station_id: int
    name: str
    charger_type: ChargerType
    status: ChargerStatus


# ---------- Stations ----------
class StationCreate(BaseModel):
    name: str
    address: str
    city: str


class StationUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None


class StationOut(OrmBase):
    id: int
    name: str
    address: str
    city: str


class StationDetail(StationOut):
    chargers: list[ChargerOut] = []


# ---------- Pricing ----------
class PricingUpdate(BaseModel):
    price_per_hour: float


class PricingOut(OrmBase):
    charger_type: ChargerType
    price_per_hour: float


# ---------- Availability ----------
class ChargerAvailability(BaseModel):
    charger_id: int
    name: str
    charger_type: ChargerType
    is_available: bool


class StationAvailability(BaseModel):
    station_id: int
    available_chargers: int
    chargers: list[ChargerAvailability]


class BookedSlot(BaseModel):
    start_time: datetime
    end_time: datetime


class ChargerSlots(BaseModel):
    charger_id: int
    status: ChargerStatus
    booked_slots: list[BookedSlot]


# ---------- Cost estimation ----------
class CostEstimateRequest(BaseModel):
    charger_id: int
    start_time: datetime
    end_time: datetime


class CostEstimateOut(BaseModel):
    hours: float
    price_per_hour: float
    estimated_cost: float


# ---------- Bookings ----------
class BookingCreate(BaseModel):
    station_id: int
    charger_id: int
    start_time: datetime
    end_time: datetime


class BookingOut(OrmBase):
    id: int
    user_id: int
    charger_id: int
    start_time: datetime
    end_time: datetime
    price_per_hour: float
    total_cost: float
    status: str
    created_at: datetime


# ---------- Admin / Revenue ----------
class DashboardOut(BaseModel):
    total_stations: int
    total_chargers: int
    available_chargers: int
    occupied_chargers: int
    maintenance_chargers: int
    total_bookings: int
    total_revenue: float


class RevenueOut(BaseModel):
    total_bookings: int
    total_revenue: float


class StationRevenueOut(BaseModel):
    station_id: int
    station_name: str
    total_bookings: int
    revenue: float
