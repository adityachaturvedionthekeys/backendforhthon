from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import health, generation
from app.core.config import settings
from app.services.image_generator import TEMP_ASSETS_DIR

app = FastAPI(title="Content Pipeline API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure assets dir exists so StaticFiles doesn't crash on startup
TEMP_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/assets", StaticFiles(directory=str(TEMP_ASSETS_DIR)), name="assets")

app.include_router(health.router)
app.include_router(generation.router, prefix=settings.api_prefix)
