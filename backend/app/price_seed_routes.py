from fastapi import APIRouter

from .database import SessionLocal
from .price_seed import seed_price_retailers

router = APIRouter()


@router.on_event("startup")
def initialize_default_price_retailers() -> None:
    with SessionLocal() as db:
        created = seed_price_retailers(db)
        if created:
            print(f"DGD-Preishändler angelegt: {created}")
