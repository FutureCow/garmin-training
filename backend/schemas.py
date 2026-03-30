from typing import Optional, List
from pydantic import BaseModel, EmailStr


# --- Auth ---

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# --- Garmin credentials ---

class GarminCredentialsRequest(BaseModel):
    garmin_username: str
    garmin_password: str


class GarminStatusResponse(BaseModel):
    connected: bool


# --- Preferences ---

class PreferencesRequest(BaseModel):
    active_days: List[str]              # e.g. ["maandag", "dinsdag", "zondag"]
    long_run_day: str
    goal_distance: str                  # "5K" | "10K" | "halve_marathon" | "marathon" | "custom"
    goal_distance_km: Optional[float] = None
    goal_pace: Optional[str] = None     # "5:30"
    goal_time: Optional[str] = None     # "1:45:00"
    schema_type: str = "fixed"          # "fixed" | "rolling"
    schema_weeks: int = 12
    start_date: Optional[str] = None    # "2026-04-07"


class PreferencesResponse(PreferencesRequest):
    class Config:
        from_attributes = True


# --- Training schemas ---

class SchemaGenerateRequest(BaseModel):
    pass  # all settings come from the stored user preferences


class DayEntry(BaseModel):
    dag: str
    type: str
    afstand_km: Optional[float] = None
    beschrijving: Optional[str] = None


class WeekEntry(BaseModel):
    week: int
    dagen: List[DayEntry]


class SchemaData(BaseModel):
    schema_type: str
    niveau: Optional[str] = None
    samenvatting: Optional[str] = None
    weken: List[WeekEntry]


class SchemaResponse(BaseModel):
    id: int
    schema_type: str
    created_at: str
    is_active: bool
    schema_data: dict

    class Config:
        from_attributes = True
