from sqlalchemy import select
from sqlalchemy.orm import Session

from .price_models import Retailer


DEFAULT_RETAILERS = [
    ("Douglas", "https://www.douglas.de"),
    ("Flaconi", "https://www.flaconi.de"),
    ("Notino", "https://www.notino.de"),
    ("Parfumdreams", "https://www.parfumdreams.de"),
    ("easycosmetic", "https://www.easycosmetic.de"),
    ("Sephora", "https://www.sephora.de"),
]


def seed_price_retailers(db: Session) -> int:
    existing = {name.casefold() for name in db.scalars(select(Retailer.name)).all()}
    created = 0
    for name, base_url in DEFAULT_RETAILERS:
        if name.casefold() in existing:
            continue
        db.add(Retailer(name=name, base_url=base_url, active=True))
        existing.add(name.casefold())
        created += 1
    if created:
        db.commit()
    return created
