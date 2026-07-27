from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .database import get_db
from .import_quality import analyze_fragrance_import, analyze_twin_import
from .import_service import parse_file

router = APIRouter(prefix="/import/quality", tags=["import-quality"])

@router.post("/preview")
async def preview_import_quality(
    file: UploadFile = File(...),
    import_type: str = Form("fragrances"),
    db: Session = Depends(get_db),
):
    if import_type not in {"fragrances", "twins"}:
        raise HTTPException(400, "Ungültiger Importtyp.")
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "Die Importdatei darf höchstens 20 MB groß sein.")
    try:
        rows = parse_file(file.filename or "", data, import_type)
        if not rows:
            raise ValueError("Die Datei enthält keine importierbaren Datenzeilen.")
        return analyze_fragrance_import(db, rows) if import_type == "fragrances" else analyze_twin_import(db, rows)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
