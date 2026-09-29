from fastapi import FastAPI
from app.api.routes import health, generation
from app.core.config import settings

app = FastAPI(title="Content Pipeline API", version="1.0.0")

app.include_router(health.router)
app.include_router(generation.router, prefix=settings.api_prefix)
