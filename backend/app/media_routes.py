import os
import re
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from .database import get_db
from .models import Fragrance


router = APIRouter(prefix="/api", tags=["media"])
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", "/app/media")).resolve()
FRAGRANCE_DIR = MEDIA_ROOT / "fragrances"
MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", str(8 * 1024 * 1024)))
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def ensure_media_dirs() -> None:
    FRAGRANCE_DIR.mkdir(parents=True, exist_ok=True)


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug[:80] or "duft"


def _looks_like_image(data: bytes, content_type: str) -> bool:
    if content_type == "image/jpeg":
        return data.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/webp":
        return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    return False


def _local_path(image_url: str | None) -> Path | None:
    prefix = "/media/fragrances/"
    if not image_url or not image_url.startswith(prefix):
        return None
    candidate = (FRAGRANCE_DIR / image_url.removeprefix(prefix)).resolve()
    try:
        candidate.relative_to(FRAGRANCE_DIR.resolve())
    except ValueError:
        return None
    return candidate


@router.post("/fragrances/{fragrance_id}/image")
async def upload_fragrance_image(
    fragrance_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    item = db.get(Fragrance, fragrance_id)
    if not item:
        raise HTTPException(404, "Duft nicht gefunden")
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(415, "Erlaubt sind JPEG, PNG und WebP.")
    data = await file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(413, f"Das Bild darf höchstens {MAX_IMAGE_BYTES // 1024 // 1024} MB groß sein.")
    if not data or not _looks_like_image(data, content_type):
        raise HTTPException(400, "Die Datei ist kein gültiges Bild des angegebenen Typs.")

    ensure_media_dirs()
    filename = f"{_safe_slug(item.brand.name)}-{_safe_slug(item.name)}-{uuid4().hex[:10]}{EXTENSIONS[content_type]}"
    target = FRAGRANCE_DIR / filename
    target.write_bytes(data)

    previous = _local_path(item.image_url)
    item.image_url = f"/media/fragrances/{filename}"
    item.image_source_name = "Lokaler DGD-Upload"
    item.image_source_url = None
    item.image_usage_note = "Lokal auf dem DGD-Unraid-Server gespeichert. Rechte und Herkunft redaktionell prüfen."
    item.image_status = "OPEN"
    db.commit()
    db.refresh(item)

    if previous and previous != target and previous.exists():
        previous.unlink(missing_ok=True)

    return {
        "image_url": item.image_url,
        "image_source_name": item.image_source_name,
        "image_usage_note": item.image_usage_note,
        "image_status": item.image_status,
        "filename": filename,
        "size_bytes": len(data),
    }


@router.delete("/fragrances/{fragrance_id}/image", status_code=204)
def delete_fragrance_image(fragrance_id: UUID, db: Session = Depends(get_db)):
    item = db.get(Fragrance, fragrance_id)
    if not item:
        raise HTTPException(404, "Duft nicht gefunden")
    local = _local_path(item.image_url)
    if not local:
        raise HTTPException(409, "Das aktuell hinterlegte Bild ist keine lokale Mediendatei.")
    local.unlink(missing_ok=True)
    item.image_url = None
    item.image_source_name = None
    item.image_source_url = None
    item.image_usage_note = None
    item.image_status = "OPEN"
    db.commit()
    return Response(status_code=204)
