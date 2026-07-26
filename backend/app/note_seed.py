from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Note, Fragrance, FragranceNote


DEFAULT_NOTES = [
    ("Aldehyde", "Synthetisch"), ("Amber", "Harzig"), ("Ambroxan", "Synthetisch"),
    ("Ananas", "Fruchtig"), ("Apfel", "Fruchtig"), ("Benzoin", "Harzig"),
    ("Bergamotte", "Zitrisch"), ("Birne", "Fruchtig"), ("Blutorange", "Zitrisch"),
    ("Cashmeran", "Synthetisch"), ("Eichenmoos", "Grün"), ("Feige", "Fruchtig"),
    ("Geranie", "Blumig"), ("Grapefruit", "Zitrisch"), ("Guajakholz", "Holzig"),
    ("Iris", "Blumig"), ("Jasmin", "Blumig"), ("Jasmin-Sambac", "Blumig"),
    ("Kaffee", "Gourmand"), ("Kakao", "Gourmand"), ("Kardamom", "Würzig"),
    ("Kaschmirholz", "Holzig"), ("Kirsche", "Fruchtig"), ("Kokos", "Gourmand"),
    ("Lavendel", "Aromatisch"), ("Leder", "Leder"), ("Limette", "Zitrisch"),
    ("Mandarine", "Zitrisch"), ("Moschus", "Moschus"), ("Moos", "Grün"),
    ("Muskatnuss", "Würzig"), ("Myrrhe", "Harzig"), ("Neroli", "Blumig"),
    ("Oud", "Holzig"), ("Patchouli", "Erdig"), ("Pfeffer", "Würzig"),
    ("Rauch", "Rauchig"), ("Rose", "Blumig"), ("Safran", "Würzig"),
    ("Sandelholz", "Holzig"), ("Tabak", "Tabak"), ("Tonkabohne", "Gourmand"),
    ("Vanille", "Gourmand"), ("Vetiver", "Erdig"), ("Weihrauch", "Harzig"),
    ("Zedernholz", "Holzig"), ("Zimt", "Würzig"), ("Zitrone", "Zitrisch"),
    ("Zypresse", "Grün"), ("Süßholz", "Würzig"), ("Trockene Hölzer", "Holzig"),
]


def normalize_name(value: str) -> str:
    return " ".join(value.strip().split())


def seed_notes(db: Session) -> None:
    existing = {
        n.casefold(): n for n in db.scalars(select(Note.name)).all()
    }
    changed = False
    for name, category in DEFAULT_NOTES:
        if name.casefold() not in existing:
            db.add(Note(name=name, category=category))
            existing[name.casefold()] = name
            changed = True
    if changed:
        db.commit()


def migrate_legacy_notes(db: Session) -> None:
    notes_by_name = {
        note.name.casefold(): note
        for note in db.scalars(select(Note)).all()
    }

    fragrances = db.scalars(select(Fragrance)).all()
    changed = False

    for fragrance in fragrances:
        already = db.scalar(
            select(FragranceNote.id)
            .where(FragranceNote.fragrance_id == fragrance.id)
            .limit(1)
        )
        if already:
            continue

        groups = [
            ("top", fragrance.top_notes),
            ("heart", fragrance.heart_notes),
            ("base", fragrance.base_notes),
        ]

        for pyramid, raw in groups:
            if not raw:
                continue
            values = [normalize_name(v) for v in raw.split(",") if normalize_name(v)]
            for position, name in enumerate(values):
                note = notes_by_name.get(name.casefold())
                if not note:
                    note = Note(name=name, category="Nicht kategorisiert")
                    db.add(note)
                    db.flush()
                    notes_by_name[name.casefold()] = note
                db.add(FragranceNote(
                    fragrance_id=fragrance.id,
                    note_id=note.id,
                    pyramid=pyramid,
                    position=position,
                ))
                changed = True

    if changed:
        db.commit()
