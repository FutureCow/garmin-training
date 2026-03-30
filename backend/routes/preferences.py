import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..config import settings
from ..database import get_db
from ..models import User, UserPreferences
from ..auth import get_current_user
from ..garmin import session_exists
from ..schemas import (
    PreferencesRequest, PreferencesResponse,
    GarminStatusResponse,
)

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=PreferencesResponse)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        raise HTTPException(status_code=404, detail="Nog geen voorkeuren ingesteld")
    return prefs


@router.put("", response_model=PreferencesResponse)
async def update_preferences(
    body: PreferencesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)

    for field, value in body.model_dump().items():
        setattr(prefs, field, value)

    await db.commit()
    await db.refresh(prefs)
    return prefs


@router.get("/garmin-status", response_model=GarminStatusResponse)
async def get_garmin_status(current_user: User = Depends(get_current_user)):
    return GarminStatusResponse(connected=session_exists(current_user.id))


@router.delete("/garmin-credentials", response_model=GarminStatusResponse)
async def delete_garmin_session(
    current_user: User = Depends(get_current_user),
):
    """Delete the saved Garmin session for this user."""
    session_dir = Path(settings.garmin_home_dir) / str(current_user.id)
    if session_dir.exists():
        shutil.rmtree(session_dir)
    return GarminStatusResponse(connected=False)
