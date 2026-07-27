from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .database import get_db
from .enrichment_routes import _scan_gaps
from .smart_gemini_runner import run_smart_gemini_research

router = APIRouter(prefix="/api/enrichment", tags=["smart-combined-research"])


@router.post("/run")
async def run_smart_combined_research(
    twin_limit: int = Query(default=5, ge=1, le=10),
    finding_limit: int = Query(default=5, ge=1, le=10),
    db: Session = Depends(get_db),
):
    gaps = _scan_gaps(db)
    research = await run_smart_gemini_research(db, min(twin_limit, finding_limit, 5))
    return {
        "gaps": gaps,
        "findings": research,
        "twins": {
            "provider": "gemini",
            "configured": research.get("configured", False),
            "created": research.get("twins_created", 0),
            "errors": research.get("errors", 0),
            "known_excluded": research.get("known_twins_excluded", 0),
        },
    }
