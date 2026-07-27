# Package initialization keeps feature routers composable without bloating main.py.
from . import research_source_models  # noqa: F401
from .research_routes import router as research_router
from .research_source_routes import router as research_source_router
from .enrichment_routes import router as enrichment_router
from .enrichment_finding_routes import router as enrichment_finding_router
from .research_enrichment import router as research_enrichment_router
from .combined_research_routes import router as combined_research_router
from .twin_workflow_routes import router as twin_workflow_router
from .targeted_research_routes import router as targeted_research_router
from .brand_research_routes import router as brand_research_router

research_router.include_router(research_source_router)
# Register the extended /api/enrichment/run before the legacy route with the same path.
research_router.routes.extend(combined_research_router.routes)
research_router.routes.extend(twin_workflow_router.routes)
research_router.routes.extend(targeted_research_router.routes)
research_router.routes.extend(brand_research_router.routes)
research_router.routes.extend(enrichment_router.routes)
research_router.routes.extend(enrichment_finding_router.routes)
research_router.routes.extend(research_enrichment_router.routes)
