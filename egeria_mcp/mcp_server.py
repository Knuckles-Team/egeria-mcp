"""Main FastMCP server and tool registration for egeria-mcp.

Granular, typed Egeria query/write tools (lineage, glossary, asset, governance)
over the pyegeria View Server surface — the deterministic routing-decision
complement to the official Dr.Egeria command/report MCP server.
"""

import os
import sys
from typing import Any

from agent_utilities.base_utilities import to_boolean
from agent_utilities.mcp_utilities import create_mcp_server
from dotenv import find_dotenv, load_dotenv
from fastmcp.utilities.logging import get_logger
from starlette.requests import Request
from starlette.responses import JSONResponse

from egeria_mcp.mcp.mcp_egeria import register_egeria_tools

__version__ = "0.2.1"
logger = get_logger(name="egeria_mcp")


def get_mcp_instance() -> tuple[Any, ...]:
    load_dotenv(find_dotenv())
    args, mcp, middlewares = create_mcp_server(
        name="Egeria MCP",
        version=__version__,
        instructions=(
            "Egeria MCP Server - granular open-metadata access over the Apache "
            "Egeria View Server (OMVS): asset catalog search, business glossary "
            "lookup, data lineage, and governance/classification reads, plus "
            "write-gated classify / create-term / assert-lineage tools."
        ),
    )

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse({"status": "OK"})

    if to_boolean(os.getenv("EGERIATOOL", "True")):
        register_egeria_tools(mcp)

    for mw in middlewares:
        mcp.add_middleware(mw)
    return mcp, args, middlewares


def mcp_server() -> None:
    mcp, args, middlewares = get_mcp_instance()
    print(f"Egeria MCP v{__version__}", file=sys.stderr)
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    mcp_server()
