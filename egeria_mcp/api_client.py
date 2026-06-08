"""Public client facade for egeria_mcp.

Re-exports :class:`~egeria_mcp.api.api_client_egeria.EgeriaApi` — the single
pyegeria-backed client used by both the MCP tools and the KG ``egeria`` enrichment
extractor (injected as ``config["client"]``). ``Api`` is kept as an alias for
parity with the other agent-packages.
"""

from egeria_mcp.api.api_client_egeria import EgeriaApi

__version__ = "0.1.0"

Api = EgeriaApi

__all__ = ["EgeriaApi", "Api"]
