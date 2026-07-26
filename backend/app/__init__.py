# Package initialization keeps feature routers composable without bloating main.py.
from . import research_source_models  # noqa: F401
from .research_routes import router as research_router
from .research_source_routes import router as research_source_router

research_router.include_router(research_source_router)
