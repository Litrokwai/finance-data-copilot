from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.sql_analysis import ApiResponse
from app.services.dashboard_service import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=ApiResponse)
def dashboard_summary(db: Session = Depends(get_db)) -> ApiResponse:
    return ApiResponse(data=get_dashboard_summary(db))
