from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.sql_analysis_record import SqlAnalysisRecord
from app.schemas.sql_analysis import ApiResponse, SqlHistoryItem

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=ApiResponse)
def list_history(db: Session = Depends(get_db)) -> ApiResponse:
    records = db.query(SqlAnalysisRecord).order_by(SqlAnalysisRecord.created_at.desc()).limit(100).all()
    return ApiResponse(data=[SqlHistoryItem.model_validate(record).model_dump(mode="json") for record in records])
