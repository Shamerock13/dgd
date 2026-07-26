# Package initialization keeps feature routers composable without bloating main.py.
from . import research_source_models  # noqa: F401
from .research_routes import router as research_router
from .research_source_routes import router as research_source_router
from .enrichment_routes import router as enrichment_router
from .enrichment_finding_routes import router as enrichment_finding_router
from .research_enrichment import router as research_enrichment_router

research_router.include_router(research_source_router)
research_router.routes.extend(enrichment_router.routes)
research_router.routes.extend(enrichment_finding_router.routes)
research_router.routes.extend(research_enrichment_router.routes)
