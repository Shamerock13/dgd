from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .database import get_db
from .models import Brand, Fragrance, FragranceNote, MasterPerfumer, MasterSource, TwinMatch


router = APIRouter(prefix="/api/quality", tags=["quality"])


def _issue(kind, entity_type, entity_id, title, detail, priority, section):
    return {
        "id": f"{kind}:{entity_type}:{entity_id}",
        "kind": kind,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "title": title,
        "detail": detail,
        "priority": priority,
        "section": section,
    }


@router.get("/worklist")
def quality_worklist(db: Session = Depends(get_db)):
    brands = list(db.scalars(select(Brand).order_by(Brand.name)))
    fragrances = list(db.scalars(select(Fragrance).options(joinedload(Fragrance.brand)).order_by(Fragrance.name)))
    twins = list(db.scalars(select(TwinMatch).options(joinedload(TwinMatch.original), joinedload(TwinMatch.alternative))))
    perfumers = list(db.scalars(select(MasterPerfumer).order_by(MasterPerfumer.name)))
    sources = list(db.scalars(select(MasterSource)))
    note_links = list(db.scalars(select(FragranceNote)))

    source_keys = {(str(row.object_type or "").upper(), str(row.object_id or "")) for row in sources}
    note_counts = Counter(str(row.fragrance_id) for row in note_links)
    perfumer_names = {row.name.strip().casefold() for row in perfumers}
    issues = []

    for brand in brands:
        if brand.verification_status != "VERIFIED":
            issues.append(_issue("brand-verification", "BRAND", brand.id, brand.name, "Markenprofil ist noch nicht verifiziert.", "HIGH", "brands"))
        missing = [label for value, label in ((brand.country, "Herkunft"), (brand.description, "Beschreibung"), (brand.website_url, "Website")) if not value]
        if missing:
            issues.append(_issue("brand-metadata", "BRAND", brand.id, brand.name, f"Fehlende Markendaten: {', '.join(missing)}.", "MEDIUM", "brands"))

    for item in fragrances:
        label = f"{item.brand.name} – {item.name}"
        if not item.image_url or item.image_status == "BROKEN":
            issues.append(_issue("fragrance-image", "FRAGRANCE", item.id, label, "Bild fehlt oder ist als fehlerhaft markiert.", "HIGH", "fragrances"))
        if ("FRAGRANCE", str(item.id)) not in source_keys:
            issues.append(_issue("fragrance-source", "FRAGRANCE", item.id, label, "Dem Duft ist noch keine Quelle zugeordnet.", "HIGH", "sources"))
        if not item.description:
            issues.append(_issue("fragrance-description", "FRAGRANCE", item.id, label, "Ausführliche Duftbeschreibung fehlt.", "MEDIUM", "fragrances"))
        if note_counts[str(item.id)] == 0 and not any((item.top_notes, item.heart_notes, item.base_notes)):
            issues.append(_issue("fragrance-notes", "FRAGRANCE", item.id, label, "Duftpyramide ist noch nicht erfasst.", "HIGH", "fragrances"))
        if not item.perfumer:
            issues.append(_issue("fragrance-perfumer", "FRAGRANCE", item.id, label, "Parfümeur ist nicht bekannt oder nicht eingetragen.", "LOW", "fragrances"))
        elif item.perfumer.strip().casefold() not in perfumer_names:
            issues.append(_issue("perfumer-profile", "FRAGRANCE", item.id, label, f"Für {item.perfumer} existiert noch kein Parfümeurprofil.", "MEDIUM", "perfumers"))

    for twin in twins:
        label = f"{twin.original.name} ↔ {twin.alternative.name}"
        if ("TWIN", str(twin.id)) not in source_keys:
            issues.append(_issue("twin-source", "TWIN", twin.id, label, "Duftzwilling hat noch keine zugeordnete Quelle.", "HIGH", "sources"))
        if not twin.commonalities or not twin.differences:
            issues.append(_issue("twin-description", "TWIN", twin.id, label, "Gemeinsamkeiten oder Unterschiede sind noch unvollständig.", "MEDIUM", "twins"))

    for perfumer in perfumers:
        if perfumer.article_status != "VERIFIED":
            issues.append(_issue("perfumer-verification", "PERFUMER", perfumer.id, perfumer.name, "Parfümeurprofil ist redaktionell noch nicht verifiziert.", "MEDIUM", "perfumers"))
        if not perfumer.primary_source:
            issues.append(_issue("perfumer-source", "PERFUMER", perfumer.id, perfumer.name, "Primärquelle fehlt.", "HIGH", "perfumers"))

    for source in sources:
        if source.trust_status in {None, "", "OPEN", "REVIEW"}:
            issues.append(_issue("source-review", "SOURCE", source.id, source.name, f"Quelle hat Vertrauensstatus {source.trust_status or 'OPEN'}.", "MEDIUM", "sources"))
        elif source.trust_status == "REJECTED":
            issues.append(_issue("source-rejected", "SOURCE", source.id, source.name, "Abgelehnte Quelle sollte ersetzt oder entfernt werden.", "HIGH", "sources"))

    rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    issues.sort(key=lambda row: (rank[row["priority"]], row["entity_type"], row["title"].casefold()))
    priorities = Counter(row["priority"] for row in issues)
    categories = Counter(row["kind"] for row in issues)
    audited_entities = len(brands) + len(fragrances) + len(twins) + len(perfumers) + len(sources)
    score = max(0, round(100 - (len(issues) / max(audited_entities, 1) * 20)))

    return {
        "summary": {
            "issues": len(issues),
            "high": priorities["HIGH"],
            "medium": priorities["MEDIUM"],
            "low": priorities["LOW"],
            "quality_score": score,
            "audited_entities": audited_entities,
        },
        "categories": dict(categories),
        "issues": issues,
    }
