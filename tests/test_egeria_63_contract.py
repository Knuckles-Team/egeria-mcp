"""Egeria 6.x support: recorded 6.3 fixtures, platform floor, docs (CONN-EGERIA-MCP-CONNECTOR-CONTENT-R004)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import httpx
import pytest

from egeria_mcp.api.api_client_egeria import (
    REMOVED_TYPES,
    SUPPORTED_FLOOR,
    TYPE_RENAMES,
    EgeriaApi,
    EgeriaPlatformVersionError,
    EgeriaUnsupportedTypeError,
    resolve_type_name,
)

ROOT = Path(__file__).resolve().parent.parent
FX = json.loads((ROOT / "tests" / "fixtures" / "egeria_63.json").read_text())


class _Platform:
    """Replays the recorded 6.3 responses; records every request."""

    def __init__(self, origin: str, create: dict | None = None) -> None:
        self.origin = origin
        self.create = create or FX["create_asset"]
        self.calls: list[tuple[str, str]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        self.calls.append((request.method, path))
        if path == "/api/token":
            return httpx.Response(200, text="tok")
        if path == "/open-metadata/platform-services/server-platform/origin":
            return httpx.Response(200, text=self.origin)
        if path.endswith("/glossaries/terms/by-search-string"):
            return httpx.Response(200, json=FX["find_terms"])
        if path.endswith("/assets/in-domain/by-search-string"):
            return httpx.Response(200, json=FX["find_assets"])
        if path.endswith("/retrieve"):
            return httpx.Response(200, json=FX["retrieve_classified"])
        if path.endswith("/as-lineage-graph"):
            return httpx.Response(200, json=FX["lineage_graph"])
        if "/lineage-linker/" in path:
            return httpx.Response(200, json=FX["link_dataflow"])
        if "/classification-explorer/" in path:
            return httpx.Response(200, json=FX["classify_confidentiality"])
        if path.endswith("/asset-maker/assets"):
            return httpx.Response(200, json=self.create)
        raise AssertionError(f"unexpected request {path}")

    def writes(self) -> list[tuple[str, str]]:
        return [
            c
            for c in self.calls
            if c[1] not in ("/api/token",)
            and "by-search-string" not in c[1]
            and "origin" not in c[1]
        ]


def _api(monkeypatch, platform: _Platform, *, write: bool = True) -> EgeriaApi:
    api = EgeriaApi(
        platform_url="https://egeria.invalid:9443",
        user_id="u",
        user_pwd="p",
        enable_write=write,
    )
    client = httpx.Client(transport=httpx.MockTransport(platform))
    monkeypatch.setattr(EgeriaApi, "_http", lambda self: client)
    return api


@pytest.mark.spec("CONN-EGERIA-MCP-CONNECTOR-CONTENT-R004")
@pytest.mark.spec("CONN-EGERIA-MCP-CONNECTOR-CONTENT-R004.1")
def test_tools_round_trip_against_the_63_type_system(monkeypatch):
    platform = _Platform(FX["platform_origin_63"])
    api = _api(monkeypatch, platform)

    # find: element header type name and flattened properties parse
    terms = api.glossary_lookup("")
    assert terms[0]["typeName"] == "GlossaryTerm"
    assert terms[0]["guid"]
    assets = api.asset_search("fx")
    assert assets and all(a["typeName"] for a in assets)

    # create: a 6.3 type is created; the version is read once and recorded
    created = api.create_asset("RelationalDatabase", "fx:db2", "db2")
    assert created["guid"].startswith("RelationalDatabase-")
    assert api._platform_status()["platformVersion"] == "6.3"
    assert api._platform_status()["writesAllowed"] is True

    # retrieve: the named Confidentiality classification and its level
    gov = api.governance_for("g")
    assert gov["confidentialityLevel"] == 3
    assert {"name": "Confidentiality", "level": 3} in gov["classifications"]

    # classify and lineage
    assert api.set_confidentiality("g", 3)["httpCode"] == 200
    assert api.link_data_flow("a", "b", label="produces")["guid"]
    graph = api.lineage("g")
    types = {
        e["relationshipHeader"]["type"]["typeName"] for e in graph["lineageLinkage"]
    }
    assert types == {"DataFlow"}

    # one origin read for the whole run
    origin_reads = [c for c in platform.calls if c[1].endswith("/origin")]
    assert len(origin_reads) == 1


@pytest.mark.spec("CONN-EGERIA-MCP-CONNECTOR-CONTENT-R004.1")
def test_removed_and_renamed_types(monkeypatch):
    # recorded 6.3 refusal for a type the platform no longer serves
    platform = _Platform(FX["platform_origin_63"], create=FX["create_removed_type"])
    api = _api(monkeypatch, platform)
    with pytest.raises(
        EgeriaUnsupportedTypeError, match="UNSUPPORTED_TYPE.*KafkaTopic"
    ):
        api.create_asset("Unknown", "fx:kt", "kt")

    # a mapped rename is applied before the call; a removed type never calls
    assert resolve_type_name("KafkaTopic") == "Topic" == TYPE_RENAMES["KafkaTopic"]
    for removed in REMOVED_TYPES:
        before = len(platform.calls)
        with pytest.raises(EgeriaUnsupportedTypeError, match=removed):
            api.create_asset(removed, f"fx:{removed}", removed)
        assert [
            c for c in platform.calls[before:] if "assets" in c[1] and c[0] == "POST"
        ] == []
    assert EgeriaUnsupportedTypeError.code == "UNSUPPORTED_TYPE"


@pytest.mark.spec("CONN-EGERIA-MCP-CONNECTOR-CONTENT-R004.2")
def test_older_platform_refuses_writes_and_names_versions(monkeypatch):
    platform = _Platform(FX["platform_origin_53"])
    api = _api(monkeypatch, platform)
    with pytest.raises(EgeriaPlatformVersionError) as err:
        api.create_asset("RelationalDatabase", "fx:db2", "db2")
    msg = str(err.value)
    assert "PLATFORM_VERSION_UNSUPPORTED" in msg and "5.3" in msg and "6.2" in msg
    assert platform.writes() == []  # no write call, no lookup either
    assert api._platform_status()["writesAllowed"] is False
    # reads still answer on an older platform
    assert api.glossary_lookup("")
    # the 6.2 floor and a 6.3 snapshot origin are accepted
    assert SUPPORTED_FLOOR == (6, 2)
    for ok in (FX["platform_origin_62"], FX["platform_origin_63"]):
        p = _Platform(ok)
        assert _api(monkeypatch, p)._platform_status()["writesAllowed"] is True


@pytest.mark.spec("CONN-EGERIA-MCP-CONNECTOR-CONTENT-R004.3")
def test_docs_name_no_5x_platform():
    pattern = re.compile(r"egeria-platform:5\.")
    files = [ROOT / "README.md", ROOT / "AGENTS.md", *(ROOT / "docs").glob("*.md")]
    files += list((ROOT / "docker").glob("*"))
    assert not [f.name for f in files if pattern.search(f.read_text())]
    platform_doc = (ROOT / "docs" / "platform.md").read_text()
    assert "odpi/egeria-platform:6." in platform_doc
    assert (
        "9b55307041770d16064e0e76abcf7a8c47ca2372649a8d4697cade9d7eca8a63"
        in platform_doc
    )
