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

__version__ = "0.2.3"
logger = get_logger(name="egeria_mcp")


def get_mcp_instance(command_args: list[str] | None = None) -> tuple[Any, ...]:
    """Build the Egeria MCP server.

    ``command_args`` is forwarded to ``create_mcp_server`` for CLI flag parsing.
    The default (``None``) parses ``sys.argv`` — correct for the ``mcp_server()``
    CLI entry point. Library/test callers should pass ``command_args=[]`` so the
    server's ``-p/--port`` parser does not consume the host process's argv (e.g.
    pytest's ``-p`` plugin flag), which would otherwise abort with ``SystemExit``.
    """
    load_dotenv(find_dotenv())
    instructions = (
        "Egeria MCP Server - granular open-metadata access over the Apache "
        "Egeria View Server (OMVS): asset catalog search, business glossary "
        "lookup, data lineage, and governance/classification reads, plus "
        "write-gated classify / create-term / assert-lineage tools."
    )
    # create_mcp_server() parses CLI flags from sys.argv. When command_args is
    # given (library/test callers), isolate sys.argv around the build so the
    # server's -p/--port parser doesn't consume the host process's argv. Done via
    # argv isolation (not a kwarg) so it works regardless of the installed
    # agent_utilities version.
    saved_argv = sys.argv
    if command_args is not None:
        sys.argv = [saved_argv[0] if saved_argv else "egeria-mcp", *command_args]
    try:
        args, mcp, middlewares = create_mcp_server(
            name="Egeria MCP",
            version=__version__,
            instructions=instructions,
        )
    finally:
        sys.argv = saved_argv

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
