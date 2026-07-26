from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .database import get_db
from .enrichment_routes import _scan_gaps
from .robust_search_service import discover_findings_robust, search_twins_robust

router = APIRouter(prefix="/api/enrichment", tags=["combined-research"])


@router.post("/run")
async def run_combined_research(
    twin_limit: int = Query(default=10, ge=1, le=30),
    finding_limit: int = Query(default=10, ge=1, le=30),
    db: Session = Depends(get_db),
):
    gaps = _scan_gaps(db)
    findings = await discover_findings_robust(db, finding_limit)
    twins = await search_twins_robust(db, twin_limit)
    return {"gaps": gaps, "findings": findings, "twins": twins}
