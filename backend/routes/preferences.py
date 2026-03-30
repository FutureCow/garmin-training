from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import User, UserPreferences
from ..auth import get_current_user, encrypt_garmin_credentials
from ..schemas import (
    PreferencesRequest, PreferencesResponse,
    GarminCredentialsRequest, GarminStatusResponse,
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


@router.put("/garmin-credentials", response_model=GarminStatusResponse)
async def update_garmin_credentials(
    body: GarminCredentialsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.garmin_credentials_encrypted = encrypt_garmin_credentials(
        body.garmin_username, body.garmin_password
    )
    db.add(current_user)
    await db.commit()
    return GarminStatusResponse(connected=True)


@router.get("/garmin-status", response_model=GarminStatusResponse)
async def get_garmin_status(current_user: User = Depends(get_current_user)):
    return GarminStatusResponse(connected=current_user.garmin_credentials_encrypted is not None)


@router.delete("/garmin-credentials", response_model=GarminStatusResponse)
async def delete_garmin_credentials(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.garmin_credentials_encrypted = None
    db.add(current_user)
    await db.commit()
    return GarminStatusResponse(connected=False)
