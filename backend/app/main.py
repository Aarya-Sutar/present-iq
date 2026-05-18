from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description="AI-powered business presentation analysis platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": settings.project_name,
        "status": "running",
        "environment": settings.environment,
    }


app.include_router(api_router, prefix=settings.api_v1_prefix)