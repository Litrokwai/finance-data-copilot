from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.sql_analysis_record import SqlAnalysisRecord


def get_dashboard_summary(db: Session) -> dict:
    total = db.query(func.count(SqlAnalysisRecord.id)).scalar() or 0
    high = db.query(func.count(SqlAnalysisRecord.id)).filter(SqlAnalysisRecord.risk_level == "HIGH").scalar() or 0
    medium = db.query(func.count(SqlAnalysisRecord.id)).filter(SqlAnalysisRecord.risk_level == "MEDIUM").scalar() or 0
    low = db.query(func.count(SqlAnalysisRecord.id)).filter(SqlAnalysisRecord.risk_level == "LOW").scalar() or 0
    since = datetime.now(UTC) - timedelta(days=7)
    recent = db.query(func.count(SqlAnalysisRecord.id)).filter(SqlAnalysisRecord.created_at >= since).scalar() or 0

    rows = (
        db.query(func.date(SqlAnalysisRecord.created_at).label("date"), func.count(SqlAnalysisRecord.id).label("count"))
        .filter(SqlAnalysisRecord.created_at >= since)
        .group_by(func.date(SqlAnalysisRecord.created_at))
        .order_by(func.date(SqlAnalysisRecord.created_at))
        .all()
    )

    return {
        "total_analysis_count": total,
        "high_risk_count": high,
        "medium_risk_count": medium,
        "low_risk_count": low,
        "recent_analysis_count": recent,
        "trend": [{"date": str(row.date), "count": row.count} for row in rows],
    }
