from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .import_quality import analyze_fragrance_import, analyze_twin_import
from .import_quality_commit import (
    ReviewDecisionError,
    apply_resolved_import,
    resolve_review_rows,
)
from .import_service import parse_file
from .models import ImportQualityRun

router = APIRouter(prefix="/import/quality", tags=["import-quality"])


def _analyze(db: Session, rows, import_type: str, row_limit: int | None = 500):
    if import_type == "fragrances":
        return analyze_fragrance_import(db, rows, row_limit=row_limit)
    return analyze_twin_import(db, rows, row_limit=row_limit)


async def _read_rows(file: UploadFile, import_type: str):
    if import_type not in {"fragrances", "twins"}:
        raise HTTPException(400, "Ungültiger Importtyp.")
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "Die Importdatei darf höchstens 20 MB groß sein.")
    try:
        rows = parse_file(file.filename or "", data, import_type)
        if not rows:
            raise ValueError("Die Datei enthält keine importierbaren Datenzeilen.")
        return rows
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


def _parse_decisions(value: str) -> Any:
    try:
        return json.loads(value or "[]")
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "Die REVIEW-Entscheidungen konnten nicht gelesen werden.") from exc


def _quality_summary(quality: dict[str, Any]) -> dict[str, Any]:
    problem_rows = [
        row for row in quality.get("rows") or []
        if row.get("action") in {"REVIEW", "BLOCK"}
    ]
    return {
        "import_type": quality.get("import_type"),
        "total_rows": quality.get("total_rows"),
        "counts": quality.get("counts") or {},
        "problem_rows": problem_rows[:100],
        "problem_rows_truncated": len(problem_rows) > 100,
    }


def _record_run(
    db: Session,
    *,
    filename: str,
    import_type: str,
    duplicate_mode: str,
    status: str,
    report: dict[str, Any],
) -> ImportQualityRun:
    run = ImportQualityRun(
        filename=filename or "import",
        import_type=import_type,
        duplicate_mode=duplicate_mode,
        status=status,
        report=report,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.post("/preview")
async def preview_import_quality(
    file: UploadFile = File(...),
    import_type: str = Form("fragrances"),
    db: Session = Depends(get_db),
):
    rows = await _read_rows(file, import_type)
    return _analyze(db, rows, import_type)


@router.get("/runs")
def list_import_quality_runs(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    rows = list(db.scalars(
        select(ImportQualityRun).order_by(ImportQualityRun.created_at.desc()).limit(limit)
    ))
    return [
        {
            "id": str(row.id),
            "filename": row.filename,
            "import_type": row.import_type,
            "duplicate_mode": row.duplicate_mode,
            "status": row.status,
            "report": row.report or {},
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


@router.post("/commit")
async def commit_import_quality(
    file: UploadFile = File(...),
    import_type: str = Form("fragrances"),
    duplicate_mode: str = Form("skip"),
    review_decisions: str = Form("[]"),
    db: Session = Depends(get_db),
):
    rows = await _read_rows(file, import_type)
    filename = file.filename or "import"
    decisions = _parse_decisions(review_decisions)
    quality = _analyze(db, rows, import_type, row_limit=None)
    counts = quality.get("counts") or {}
    block_count = int(counts.get("BLOCK") or 0)

    if block_count:
        report = {
            "message": "Der Import enthält blockierte Zeilen.",
            "quality": _quality_summary(quality),
            "decisions": decisions,
        }
        run = _record_run(
            db,
            filename=filename,
            import_type=import_type,
            duplicate_mode=duplicate_mode,
            status="BLOCKED",
            report=report,
        )
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Der Import wurde durch blockierte Zeilen gestoppt.",
                "run_id": str(run.id),
                "review_count": int(counts.get("REVIEW") or 0),
                "block_count": block_count,
                "quality": _quality_summary(quality),
            },
        )

    try:
        resolved_rows, decision_report, excluded = resolve_review_rows(
            rows,
            import_type,
            quality,
            decisions,
        )
        result = apply_resolved_import(db, resolved_rows, import_type, duplicate_mode)
        report = {
            "quality": _quality_summary(quality),
            "decisions": decision_report,
            "excluded": excluded,
            "result": result,
        }
        run = ImportQualityRun(
            filename=filename,
            import_type=import_type,
            duplicate_mode=duplicate_mode,
            status="SUCCESS",
            report=report,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return {
            **result,
            "excluded": excluded,
            "quality_counts": counts,
            "quality_checked": True,
            "review_decisions": decision_report,
            "run_id": str(run.id),
        }
    except ReviewDecisionError as exc:
        db.rollback()
        report = {
            "message": str(exc),
            "quality": _quality_summary(quality),
            "decisions": decisions,
        }
        run = _record_run(
            db,
            filename=filename,
            import_type=import_type,
            duplicate_mode=duplicate_mode,
            status="BLOCKED",
            report=report,
        )
        raise HTTPException(
            status_code=409,
            detail={
                "message": str(exc),
                "run_id": str(run.id),
                "review_count": int(counts.get("REVIEW") or 0),
                "block_count": 0,
                "quality": _quality_summary(quality),
            },
        ) from exc
    except Exception as exc:
        db.rollback()
        try:
            _record_run(
                db,
                filename=filename,
                import_type=import_type,
                duplicate_mode=duplicate_mode,
                status="FAILED",
                report={"message": str(exc), "quality": _quality_summary(quality)},
            )
        except Exception:
            db.rollback()
        raise
