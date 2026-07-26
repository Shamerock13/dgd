# Register media endpoints on the existing quality router before app.main imports it.
from . import media_routes as _media_routes  # noqa: F401
