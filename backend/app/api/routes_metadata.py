from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.sql_analysis import ApiResponse
from app.services.metadata_service import (
    get_metadata_graph,
    get_metadata_summary,
    get_metadata_table_detail,
    list_metadata_tables,
)

router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.get("/summary", response_model=ApiResponse)
def metadata_summary(db: Session = Depends(get_db)) -> ApiResponse:
    return ApiResponse(data=get_metadata_summary(db))


@router.get("/tables", response_model=ApiResponse)
def metadata_tables(
    keyword: str | None = Query(default=None),
    business_domain: str | None = Query(default=None),
    is_valid: bool | None = Query(default=None),
    sort_by: str | None = Query(default=None),
    sort_order: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ApiResponse:
    return ApiResponse(
        data=list_metadata_tables(db, keyword, business_domain, is_valid, page, page_size, sort_by, sort_order)
    )


@router.get("/tables/{table_id}", response_model=ApiResponse)
def metadata_table_detail(table_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    detail = get_metadata_table_detail(db, table_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="metadata table not found")
    return ApiResponse(data=detail)


@router.get("/graph", response_model=ApiResponse)
def metadata_graph(db: Session = Depends(get_db)) -> ApiResponse:
    return ApiResponse(data=get_metadata_graph(db))
