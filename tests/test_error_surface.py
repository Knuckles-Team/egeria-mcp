"""An unreachable or failing Egeria platform surfaces as a typed MCP tool error."""

from __future__ import annotations

import asyncio

import httpx
import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from egeria_mcp.api.api_client_egeria import (
    EgeriaApi,
    EgeriaApiError,
    EgeriaUnavailableError,
)

TERMS = {
    "class": "ElementsResponse",
    "relatedHTTPCode": 200,
    "elements": [
        {
            "elementHeader": {"guid": "g-1", "type": {"typeName": "GlossaryTerm"}},
            "properties": {"displayName": "Customer", "qualifiedName": "T::Customer"},
        }
    ],
}


def _api(monkeypatch, handler) -> EgeriaApi:
    api = EgeriaApi(
        platform_url="https://egeria.invalid:9443", user_id="u", user_pwd="p"
    )
    client = httpx.Client(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(EgeriaApi, "_http", lambda self: client)
    return api


def _handler(search_response):
    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/token":
            return httpx.Response(200, text="jwt-token")
        return search_response(request)

    return handle


def _call_tool(api: EgeriaApi):
    mcp = FastMCP("egeria-test")

    @mcp.tool
    def egeria_list_glossary_terms() -> list[dict]:
        return api.list_glossary_terms()

    async def run():
        async with Client(mcp) as c:
            return await c.call_tool("egeria_list_glossary_terms", {})

    return asyncio.run(run())


@pytest.mark.spec("CONN-EGERIA-MCP-ERROR-SURFACE-R001")
def test_connection_refused_is_a_tool_error(monkeypatch):
    def refuse(request):
        raise httpx.ConnectError("connection refused")

    api = _api(monkeypatch, refuse)
    with pytest.raises(EgeriaUnavailableError, match="unreachable"):
        api.list_glossary_terms()
    with pytest.raises(ToolError, match="unreachable"):
        _call_tool(api)


@pytest.mark.spec("CONN-EGERIA-MCP-ERROR-SURFACE-R001")
def test_http_503_is_unavailable(monkeypatch):
    api = _api(monkeypatch, _handler(lambda r: httpx.Response(503, text="down")))
    with pytest.raises(EgeriaUnavailableError, match="503"):
        api.list_glossary_terms()


@pytest.mark.spec("CONN-EGERIA-MCP-ERROR-SURFACE-R002")
def test_in_body_503_is_a_tool_error(monkeypatch):
    body = {
        "class": "VoidResponse",
        "relatedHTTPCode": 503,
        "exceptionClassName": "OMAGMultiTenantException",
        "exceptionErrorMessage": "server is not running",
    }
    api = _api(monkeypatch, _handler(lambda r: httpx.Response(200, json=body)))
    with pytest.raises(ToolError, match="server is not running"):
        _call_tool(api)


@pytest.mark.spec("CONN-EGERIA-MCP-ERROR-SURFACE-R002")
def test_in_body_client_error_is_api_error(monkeypatch):
    body = {
        "relatedHTTPCode": 400,
        "exceptionClassName": "InvalidParameterException",
        "exceptionErrorMessage": "bad searchString",
    }
    api = _api(monkeypatch, _handler(lambda r: httpx.Response(200, json=body)))
    with pytest.raises(EgeriaApiError) as ei:
        api.list_glossary_terms()
    assert ei.value.related_http_code == 400


@pytest.mark.spec("CONN-EGERIA-MCP-ERROR-SURFACE-R003")
def test_normal_200_returns_data(monkeypatch):
    api = _api(monkeypatch, _handler(lambda r: httpx.Response(200, json=TERMS)))
    out = api.list_glossary_terms()
    assert [t["displayName"] for t in out] == ["Customer"]
    result = _call_tool(api)
    assert result.is_error is False
    assert api.list_glossary_terms() == out


@pytest.mark.spec("CONN-EGERIA-MCP-ERROR-SURFACE-R003")
def test_genuine_empty_result_is_not_an_error(monkeypatch):
    empty = {"relatedHTTPCode": 200, "elements": []}
    api = _api(monkeypatch, _handler(lambda r: httpx.Response(200, json=empty)))
    assert api.list_glossary_terms() == []
