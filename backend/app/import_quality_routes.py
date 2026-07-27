from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .database import get_db
from .import_quality import analyze_fragrance_import, analyze_twin_import
from .import_service import commit_import, parse_file

router = APIRouter(prefix="/import/quality", tags=["import-quality"])


def _analyze(db: Session, rows, import_type: str):
    return analyze_fragrance_import(db, rows) if import_type == "fragrances" else analyze_twin_import(db, rows)


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


@router.post("/preview")
async def preview_import_quality(
    file: UploadFile = File(...),
    import_type: str = Form("fragrances"),
    db: Session = Depends(get_db),
):
    rows = await _read_rows(file, import_type)
    return _analyze(db, rows, import_type)


@router.post("/commit")
async def commit_import_quality(
    file: UploadFile = File(...),
    import_type: str = Form("fragrances"),
    duplicate_mode: str = Form("skip"),
    db: Session = Depends(get_db),
):
    rows = await _read_rows(file, import_type)
    quality = _analyze(db, rows, import_type)
    counts = quality.get("counts") or {}
    review_count = int(counts.get("REVIEW") or 0)
    block_count = int(counts.get("BLOCK") or 0)
    if review_count or block_count:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Der Import wurde durch die Qualitätsprüfung gestoppt.",
                "review_count": review_count,
                "block_count": block_count,
                "quality": quality,
            },
        )
    result = commit_import(db, rows, import_type, duplicate_mode)
    return {**result, "quality_counts": counts, "quality_checked": True}
