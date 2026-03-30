from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes import auth as auth_router
from .routes import preferences as prefs_router
from .routes import schemas as schemas_router

app = FastAPI(title="Garmin Training App")

app.include_router(auth_router.router)
app.include_router(prefs_router.router)
app.include_router(schemas_router.router)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
