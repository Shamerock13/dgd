from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .database import get_db
from .enrichment_routes import _scan_gaps, _search_twins
from .research_enrichment import discover_findings

router = APIRouter(prefix="/api/enrichment", tags=["combined-research"])


@router.post("/run")
async def run_combined_research(
    twin_limit: int = Query(default=10, ge=1, le=30),
    finding_limit: int = Query(default=10, ge=1, le=30),
    db: Session = Depends(get_db),
):
    gaps = _scan_gaps(db)
    findings = await discover_findings(db, finding_limit)
    twins = await _search_twins(db, twin_limit)
    return {"gaps": gaps, "findings": findings, "twins": twins}
