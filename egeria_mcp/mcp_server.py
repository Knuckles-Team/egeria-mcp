"""Main FastMCP server and tool registration for egeria-mcp.

Granular, typed Egeria query/write tools (lineage, glossary, asset, governance)
over the pyegeria View Server surface — the deterministic routing-decision
complement to the official Dr.Egeria command/report MCP server.
"""

from egeria_mcp.mcp.mcp_egeria import register_egeria_tools  # noqa: F401

# SDK discovery registers the register_<tag>_tools functions bound in this module.
__all__ = ["register_egeria_tools"]
