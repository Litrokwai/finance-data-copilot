from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.sql_analysis import ApiResponse
from app.services.procedure_lineage_service import (
    get_lineage_summary,
    get_procedure_lineage_detail,
    get_procedure_lineage_graph,
    get_table_impact,
    list_lineage_tables,
    list_procedure_lineage,
)

router = APIRouter(prefix="/lineage", tags=["lineage"])


@router.get("/summary", response_model=ApiResponse)
def lineage_summary(db: Session = Depends(get_db)) -> ApiResponse:
    return ApiResponse(data=get_lineage_summary(db))


@router.get("/procedures", response_model=ApiResponse)
def lineage_procedures(
    keyword: str | None = Query(default=None),
    parse_status: str | None = Query(default=None, pattern="^(SUCCESS|REVIEW)$"),
    db: Session = Depends(get_db),
) -> ApiResponse:
    return ApiResponse(data=list_procedure_lineage(db, keyword, parse_status))


@router.get("/procedures/{record_id}", response_model=ApiResponse)
def lineage_procedure_detail(record_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    detail = get_procedure_lineage_detail(db, record_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="procedure lineage record not found")
    return ApiResponse(data=detail)


@router.get("/tables", response_model=ApiResponse)
def lineage_tables(
    keyword: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> ApiResponse:
    return ApiResponse(data=list_lineage_tables(db, keyword, limit))


@router.get("/table-impact", response_model=ApiResponse)
def lineage_table_impact(table_name: str = Query(min_length=1), db: Session = Depends(get_db)) -> ApiResponse:
    return ApiResponse(data=get_table_impact(db, table_name))


@router.get("/graph", response_model=ApiResponse)
def lineage_graph(
    keyword: str | None = Query(default=None),
    parse_status: str | None = Query(default=None, pattern="^(SUCCESS|REVIEW)$"),
    max_procedures: int = Query(default=80, ge=1, le=300),
    db: Session = Depends(get_db),
) -> ApiResponse:
    return ApiResponse(data=get_procedure_lineage_graph(db, keyword, max_procedures, parse_status))
