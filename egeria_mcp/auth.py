"""Identity / connection loader for the Egeria client facade."""

from agent_utilities.base_utilities import get_logger
from agent_utilities.core.config import setting
from agent_utilities.core.transport_security import resolve_configured_tls_profile

from egeria_mcp.api_client import EgeriaApi

logger = get_logger(__name__)


def get_client() -> EgeriaApi:
    """Build a configured :class:`EgeriaApi` from the environment.

    Environment (names match the official Dr.Egeria MCP server):
        ``EGERIA_PLATFORM_URL``   OMAG platform URL (default ``https://localhost:9443``)
        ``EGERIA_VIEW_SERVER``    View server name (default ``qs-view-server``)
        ``EGERIA_USER``           User id (required)
        ``EGERIA_USER_PASSWORD``  Password / token (required)
        ``EGERIA_TLS_PROFILE``    Runtime TLS profile selector (optional)
        ``EGERIA_ENABLE_WRITE``   Allow classify/create/lineage writes (default ``False``)
    """
    return EgeriaApi(
        platform_url=setting("EGERIA_PLATFORM_URL", "https://localhost:9443"),
        view_server=setting("EGERIA_VIEW_SERVER", "qs-view-server"),
        user_id=setting("EGERIA_USER"),
        user_pwd=setting("EGERIA_USER_PASSWORD"),
        tls_profile=resolve_configured_tls_profile(
            "EGERIA",
            profile_name=setting("EGERIA_TLS_PROFILE"),
        ),
        enable_write=setting("EGERIA_ENABLE_WRITE", False),
    )
