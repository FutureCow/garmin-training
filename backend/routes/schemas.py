from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..database import get_db
from ..models import User, UserPreferences, TrainingSchema
from ..auth import get_current_user
from ..scheduler import generate_training_schedule
from ..schemas import SchemaResponse

router = APIRouter(prefix="/schemas", tags=["schemas"])


@router.post("/generate", response_model=SchemaResponse, status_code=201)
async def generate_schema(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.garmin_credentials_encrypted:
        raise HTTPException(status_code=400, detail="Geen Garmin-account gekoppeld")

    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        raise HTTPException(status_code=400, detail="Stel eerst voorkeuren in")

    prefs_dict = {
        "active_days": prefs.active_days,
        "long_run_day": prefs.long_run_day,
        "goal_distance": prefs.goal_distance,
        "goal_distance_km": prefs.goal_distance_km,
        "goal_pace": prefs.goal_pace,
        "goal_time": prefs.goal_time,
        "schema_type": prefs.schema_type,
        "schema_weeks": prefs.schema_weeks,
        "start_date": prefs.start_date,
    }

    schema_data = await generate_training_schedule(
        current_user.garmin_credentials_encrypted,
        prefs_dict,
    )

    # Deactivate previous active schemas
    await db.execute(
        update(TrainingSchema)
        .where(TrainingSchema.user_id == current_user.id, TrainingSchema.is_active == True)
        .values(is_active=False)
    )

    new_schema = TrainingSchema(
        user_id=current_user.id,
        schema_type=prefs.schema_type,
        schema_data=schema_data,
        is_active=True,
    )
    db.add(new_schema)
    await db.commit()
    await db.refresh(new_schema)

    return _to_response(new_schema)


@router.get("", response_model=list[SchemaResponse])
async def list_schemas(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrainingSchema)
        .where(TrainingSchema.user_id == current_user.id)
        .order_by(TrainingSchema.created_at.desc())
    )
    return [_to_response(s) for s in result.scalars().all()]


@router.get("/active", response_model=SchemaResponse)
async def get_active_schema(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrainingSchema).where(
            TrainingSchema.user_id == current_user.id,
            TrainingSchema.is_active == True,
        )
    )
    schema = result.scalar_one_or_none()
    if not schema:
        raise HTTPException(status_code=404, detail="Geen actief schema")
    return _to_response(schema)


@router.get("/{schema_id}", response_model=SchemaResponse)
async def get_schema(
    schema_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrainingSchema).where(
            TrainingSchema.id == schema_id,
            TrainingSchema.user_id == current_user.id,
        )
    )
    schema = result.scalar_one_or_none()
    if not schema:
        raise HTTPException(status_code=404, detail="Schema niet gevonden")
    return _to_response(schema)


def _to_response(schema: TrainingSchema) -> SchemaResponse:
    return SchemaResponse(
        id=schema.id,
        schema_type=schema.schema_type,
        created_at=schema.created_at.isoformat(),
        is_active=schema.is_active,
        schema_data=schema.schema_data,
    )
