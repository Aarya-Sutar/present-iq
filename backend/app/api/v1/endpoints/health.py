from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db.session import engine

router = APIRouter()


@router.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "connected",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"database unavailable: {exc}",
        ) from exc