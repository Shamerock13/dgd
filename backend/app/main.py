from uuid import UUID
import os
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, Query, HTTPException, Response, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func, or_, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from .database import Base, engine, SessionLocal, get_db
from .models import Brand, Fragrance, TwinMatch, Note, FragranceNote, MasterImportRun
from .schemas import (
    BrandCreate, BrandUpdate, BrandOut,
    FragranceCreate, FragranceUpdate, FragranceOut,
    TwinCreate, TwinOut,
    NoteCreate, NoteUpdate, NoteOut,
    FragranceNoteAssignment, FragranceNoteOut,
)
from .seed import seed_database
from .note_seed import seed_notes, migrate_legacy_notes
from .import_service import parse_file, preview_import, commit_import
from .master_import_service import (
    MasterImportValidationError, preview_master_import, commit_master_import,
)
from .migrations import run_migrations, current_schema_version, migration_history
from .update_service import updater_request
from .source_routes import router as source_router

STATIC_DIR = Path(__file__).parent / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Neue Tabellen zuerst anlegen, bestehende Tabellen anschließend erweitern.
    Base.metadata.create_all(bind=engine)
    applied = run_migrations(engine)
    # Noch einmal ausführen, damit auch zukünftige migrationsabhängige Tabellen
    # zuverlässig auf dem vollständigen Schema basieren.
    Base.metadata.create_all(bind=engine)

    if applied:
        print(f"DGD-Datenbankmigrationen angewendet: {', '.join(applied)}")
    else:
        print(f"DGD-Datenbankschema aktuell: {current_schema_version(engine)}")

    if os.getenv("AUTO_SEED", "true").lower() in {"1", "true", "yes", "on"}:
        with SessionLocal() as db:
            seed_database(db)
            seed_notes(db)
            migrate_legacy_notes(db)
    yield

app = FastAPI(title="DGD API", version="1.2.0", lifespan=lifespan)
app.include_router(source_router)

def fragrance_query():
    return select(Fragrance).options(joinedload(Fragrance.brand))

def twin_query():
    return select(TwinMatch).options(
        joinedload(TwinMatch.original).joinedload(Fragrance.brand),
        joinedload(TwinMatch.alternative).joinedload(Fragrance.brand),
    )

def twin_to_out(row: TwinMatch) -> TwinOut:
    return TwinOut(
        id=row.id, original=row.original, alternative=row.alternative,
        similarity=row.similarity, differences=row.differences,
        commonalities=row.commonalities, source_note=row.source_note
    )

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.2.0", "schema_version": current_schema_version(engine)}


@app.get("/api/system/migrations")
def system_migrations():
    return {
        "schema_version": current_schema_version(engine),
        "history": migration_history(engine),
    }


@app.get("/api/system/updates")
async def system_updates():
    return await updater_request("GET", "/api/updates")


@app.get("/api/system/updates/status")
async def system_update_status():
    return await updater_request("GET", "/api/status")



@app.get("/api/system/updates/diagnostics")
async def system_update_diagnostics():
    return await updater_request("GET", "/api/diagnostics")

@app.post("/api/system/updates/rescan")
async def system_update_rescan():
    return await updater_request("POST", "/api/rescan")


@app.post("/api/system/updates/{package_id}/install", status_code=202)
async def system_update_install(package_id: str):
    if not package_id or len(package_id) > 180 or "/" in package_id or "\\" in package_id:
        raise HTTPException(400, "Ungültige Paket-ID")
    return await updater_request(
        "POST",
        f"/api/updates/{package_id}/install",
        timeout=30.0,
    )

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return {
        "fragrances": db.scalar(select(func.count(Fragrance.id))) or 0,
        "brands": db.scalar(select(func.count(Brand.id))) or 0,
        "twins": db.scalar(select(func.count(TwinMatch.id))) or 0,
        "average_similarity": round(db.scalar(select(func.avg(TwinMatch.similarity))) or 0, 1),
        "notes": db.scalar(select(func.count(Note.id))) or 0,
    }

@app.get("/api/brands", response_model=list[BrandOut])
def brands(db: Session = Depends(get_db)):
    return list(db.scalars(select(Brand).order_by(Brand.name)))

@app.post("/api/brands", response_model=BrandOut, status_code=201)
def create_brand(payload: BrandCreate, db: Session = Depends(get_db)):
    item = Brand(**payload.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Diese Marke existiert bereits.")
    db.refresh(item)
    return item

@app.put("/api/brands/{brand_id}", response_model=BrandOut)
def update_brand(brand_id: UUID, payload: BrandUpdate, db: Session = Depends(get_db)):
    item = db.get(Brand, brand_id)
    if not item:
        raise HTTPException(404, "Marke nicht gefunden")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Der Markenname ist bereits vergeben.")
    db.refresh(item)
    return item

@app.delete("/api/brands/{brand_id}", status_code=204)
def delete_brand(brand_id: UUID, db: Session = Depends(get_db)):
    item = db.get(Brand, brand_id)
    if not item:
        raise HTTPException(404, "Marke nicht gefunden")
    has_fragrances = db.scalar(select(func.count(Fragrance.id)).where(Fragrance.brand_id == brand_id))
    if has_fragrances:
        raise HTTPException(409, "Die Marke kann nicht gelöscht werden, solange ihr Düfte zugeordnet sind.")
    db.delete(item)
    db.commit()
    return Response(status_code=204)

@app.get("/api/fragrances", response_model=list[FragranceOut])
def fragrances(
    q: str | None = Query(default=None, max_length=120),
    gender: str | None = None,
    max_price: float | None = None,
    min_longevity: float | None = None,
    db: Session = Depends(get_db),
):
    stmt = fragrance_query().join(Brand)
    if q:
        pattern = f"%{q.strip()}%"
        matching_note_fragrances = (
            select(FragranceNote.fragrance_id)
            .join(Note, Note.id == FragranceNote.note_id)
            .where(Note.name.ilike(pattern))
        )
        stmt = stmt.where(or_(
            Fragrance.name.ilike(pattern), Brand.name.ilike(pattern),
            Fragrance.accords.ilike(pattern), Fragrance.top_notes.ilike(pattern),
            Fragrance.heart_notes.ilike(pattern), Fragrance.base_notes.ilike(pattern),
            Fragrance.id.in_(matching_note_fragrances),
        ))
    if gender:
        stmt = stmt.where(Fragrance.gender == gender)
    if max_price is not None:
        stmt = stmt.where(Fragrance.price_eur <= max_price)
    if min_longevity is not None:
        stmt = stmt.where(Fragrance.longevity >= min_longevity)
    return list(db.scalars(stmt.order_by(Brand.name, Fragrance.name)).unique())

@app.get("/api/fragrances/{fragrance_id}", response_model=FragranceOut)
def fragrance(fragrance_id: UUID, db: Session = Depends(get_db)):
    item = db.scalar(fragrance_query().where(Fragrance.id == fragrance_id))
    if not item:
        raise HTTPException(404, "Duft nicht gefunden")
    return item

@app.post("/api/fragrances", response_model=FragranceOut, status_code=201)
def create_fragrance(payload: FragranceCreate, db: Session = Depends(get_db)):
    if not db.get(Brand, payload.brand_id):
        raise HTTPException(400, "Die gewählte Marke existiert nicht.")
    item = Fragrance(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return db.scalar(fragrance_query().where(Fragrance.id == item.id))

@app.put("/api/fragrances/{fragrance_id}", response_model=FragranceOut)
def update_fragrance(fragrance_id: UUID, payload: FragranceUpdate, db: Session = Depends(get_db)):
    item = db.get(Fragrance, fragrance_id)
    if not item:
        raise HTTPException(404, "Duft nicht gefunden")
    if not db.get(Brand, payload.brand_id):
        raise HTTPException(400, "Die gewählte Marke existiert nicht.")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    db.commit()
    return db.scalar(fragrance_query().where(Fragrance.id == item.id))

@app.delete("/api/fragrances/{fragrance_id}", status_code=204)
def delete_fragrance(fragrance_id: UUID, db: Session = Depends(get_db)):
    item = db.get(Fragrance, fragrance_id)
    if not item:
        raise HTTPException(404, "Duft nicht gefunden")
    db.execute(delete(FragranceNote).where(FragranceNote.fragrance_id == fragrance_id))
    db.query(TwinMatch).filter(
        or_(TwinMatch.original_id == fragrance_id, TwinMatch.alternative_id == fragrance_id)
    ).delete(synchronize_session=False)
    db.delete(item)
    db.commit()
    return Response(status_code=204)



@app.post("/api/import/preview")
async def import_preview(
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
        return preview_import(db, rows, import_type)
    except (ValueError, zipfile.BadZipFile) as exc:
        raise HTTPException(400, str(exc))


@app.post("/api/import/commit")
async def import_commit(
    file: UploadFile = File(...),
    import_type: str = Form("fragrances"),
    duplicate_mode: str = Form("skip"),
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
        return commit_import(db, rows, import_type, duplicate_mode)
    except (ValueError, zipfile.BadZipFile) as exc:
        raise HTTPException(400, str(exc))

@app.post("/api/import/master/preview")
async def master_import_preview(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "Die Importdatei darf höchstens 20 MB groß sein.")
    try:
        return preview_master_import(db, data, file.filename or "master.xlsx")
    except MasterImportValidationError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/import/master/commit")
async def master_import_commit(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "Die Importdatei darf höchstens 20 MB groß sein.")
    try:
        return commit_master_import(db, data, file.filename or "master.xlsx")
    except MasterImportValidationError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/import/master/runs")
def master_import_runs(limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    rows = list(db.scalars(
        select(MasterImportRun).order_by(MasterImportRun.created_at.desc()).limit(limit)
    ))
    return [
        {
            "id": str(row.id),
            "filename": row.filename,
            "file_version": row.file_version,
            "status": row.status,
            "report": row.report or {},
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


@app.get("/api/notes", response_model=list[NoteOut])
def notes(
    q: str | None = Query(default=None, max_length=100),
    category: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Note)
    if q:
        stmt = stmt.where(Note.name.ilike(f"%{q.strip()}%"))
    if category:
        stmt = stmt.where(Note.category == category)
    return list(db.scalars(stmt.order_by(Note.category, Note.name)))


@app.post("/api/notes", response_model=NoteOut, status_code=201)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)):
    item = Note(**payload.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Diese Duftnote existiert bereits.")
    db.refresh(item)
    return item


@app.put("/api/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: UUID, payload: NoteUpdate, db: Session = Depends(get_db)):
    item = db.get(Note, note_id)
    if not item:
        raise HTTPException(404, "Duftnote nicht gefunden")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Der Name dieser Duftnote ist bereits vergeben.")
    db.refresh(item)
    return item


@app.delete("/api/notes/{note_id}", status_code=204)
def delete_note(note_id: UUID, db: Session = Depends(get_db)):
    item = db.get(Note, note_id)
    if not item:
        raise HTTPException(404, "Duftnote nicht gefunden")
    used = db.scalar(
        select(func.count(FragranceNote.id))
        .where(FragranceNote.note_id == note_id)
    )
    if used:
        raise HTTPException(
            409,
            f"Diese Duftnote wird noch in {used} Zuordnung(en) verwendet."
        )
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@app.get(
    "/api/fragrances/{fragrance_id}/notes",
    response_model=list[FragranceNoteOut]
)
def fragrance_notes(fragrance_id: UUID, db: Session = Depends(get_db)):
    if not db.get(Fragrance, fragrance_id):
        raise HTTPException(404, "Duft nicht gefunden")
    stmt = (
        select(FragranceNote)
        .options(joinedload(FragranceNote.note))
        .where(FragranceNote.fragrance_id == fragrance_id)
        .order_by(FragranceNote.pyramid, FragranceNote.position)
    )
    return list(db.scalars(stmt).unique())


@app.put(
    "/api/fragrances/{fragrance_id}/notes",
    response_model=list[FragranceNoteOut]
)
def replace_fragrance_notes(
    fragrance_id: UUID,
    payload: list[FragranceNoteAssignment],
    db: Session = Depends(get_db),
):
    fragrance = db.get(Fragrance, fragrance_id)
    if not fragrance:
        raise HTTPException(404, "Duft nicht gefunden")

    note_ids = {entry.note_id for entry in payload}
    existing_ids = set(
        db.scalars(select(Note.id).where(Note.id.in_(note_ids))).all()
    ) if note_ids else set()
    missing = note_ids - existing_ids
    if missing:
        raise HTTPException(400, "Mindestens eine gewählte Duftnote existiert nicht.")

    db.execute(
        delete(FragranceNote)
        .where(FragranceNote.fragrance_id == fragrance_id)
    )

    for entry in payload:
        db.add(FragranceNote(
            fragrance_id=fragrance_id,
            note_id=entry.note_id,
            pyramid=entry.pyramid,
            position=entry.position,
        ))

    # Freitextfelder automatisch synchron halten.
    notes_by_id = {
        note.id: note
        for note in db.scalars(select(Note).where(Note.id.in_(note_ids))).all()
    } if note_ids else {}

    grouped = {"top": [], "heart": [], "base": []}
    for entry in sorted(payload, key=lambda x: (x.pyramid, x.position)):
        grouped[entry.pyramid].append(notes_by_id[entry.note_id].name)

    fragrance.top_notes = ", ".join(grouped["top"]) or None
    fragrance.heart_notes = ", ".join(grouped["heart"]) or None
    fragrance.base_notes = ", ".join(grouped["base"]) or None

    db.commit()

    stmt = (
        select(FragranceNote)
        .options(joinedload(FragranceNote.note))
        .where(FragranceNote.fragrance_id == fragrance_id)
        .order_by(FragranceNote.pyramid, FragranceNote.position)
    )
    return list(db.scalars(stmt).unique())

@app.get("/api/twins", response_model=list[TwinOut])
def twins(db: Session = Depends(get_db)):
    rows = list(db.scalars(twin_query().order_by(TwinMatch.similarity.desc())).unique())
    return [twin_to_out(row) for row in rows]

@app.post("/api/twins", response_model=TwinOut, status_code=201)
def create_twin(payload: TwinCreate, db: Session = Depends(get_db)):
    if payload.original_id == payload.alternative_id:
        raise HTTPException(400, "Original und Alternative müssen unterschiedliche Düfte sein.")
    if not db.get(Fragrance, payload.original_id) or not db.get(Fragrance, payload.alternative_id):
        raise HTTPException(400, "Mindestens einer der ausgewählten Düfte existiert nicht.")
    item = TwinMatch(**payload.model_dump())
    db.add(item)
    db.commit()
    row = db.scalar(twin_query().where(TwinMatch.id == item.id))
    return twin_to_out(row)

@app.delete("/api/twins/{twin_id}", status_code=204)
def delete_twin(twin_id: UUID, db: Session = Depends(get_db)):
    item = db.get(TwinMatch, twin_id)
    if not item:
        raise HTTPException(404, "Duftzwilling nicht gefunden")
    db.delete(item)
    db.commit()
    return Response(status_code=204)

if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

@app.get("/{full_path:path}")
def spa(full_path: str):
    requested = STATIC_DIR / full_path
    if full_path and requested.is_file():
        return FileResponse(requested)
    return FileResponse(STATIC_DIR / "index.html")
