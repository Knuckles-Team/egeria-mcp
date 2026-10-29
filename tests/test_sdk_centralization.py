"""The connector runs on the SDK governed client, credential resolver and extras."""

from __future__ import annotations

import pathlib

import pytest
import tomllib

from egeria_mcp.governed_http import governed_client
from egeria_mcp.harvest import secrets

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.mark.spec("CONN-EGERIA-MCP-SDK-CENTRALIZATION-R001")
def test_no_direct_httpx_client():
    offenders = [
        str(p.relative_to(ROOT))
        for p in (ROOT / "egeria_mcp").rglob("*.py")
        if "httpx.Client(" in p.read_text() and p.name != "governed_http.py"
    ]
    assert offenders == []
    with governed_client("https://egeria.invalid") as client:
        assert client.is_closed is False


@pytest.mark.spec("CONN-EGERIA-MCP-SDK-CENTRALIZATION-R002")
def test_openbao_token_reference_is_resolved(monkeypatch):
    monkeypatch.setenv("EGERIA_TEST_TOKEN", "tok-value")
    monkeypatch.setenv("OPENBAO_TOKEN_REF", "env://EGERIA_TEST_TOKEN")
    monkeypatch.delenv("OPENBAO_TOKEN", raising=False)
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    assert secrets._token(None) == "tok-value"
    monkeypatch.setenv("OPENBAO_TOKEN_REF", "env://EGERIA_MISSING_TOKEN")
    assert secrets._token(None) is None


@pytest.mark.spec("CONN-EGERIA-MCP-SDK-CENTRALIZATION-R003")
def test_database_driver_comes_from_sdk_extra():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    extras = project["optional-dependencies"]
    for name in ("harvest", "all"):
        pins = extras[name]
        assert any(p.startswith("scion-sdk[") and "db" in p for p in pins)
        assert not any(p.startswith("pymongo") for p in pins)
