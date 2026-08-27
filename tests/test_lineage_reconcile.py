"""CA-46: egeria_lineage_scan / egeria_reconcile_openlineage_asset / egeria_asset_for_kg_node.

Exercises the three new lineage-domain tools' underlying functions with a fake
Egeria client (no network): the OpenLineage-asset reconcile's fresh-create,
idempotent-rerun, and malformed-namespace-quarantine cases (CA-46-W04); that
``egeria_lineage_scan`` matches ``lineage_scan.catalog_lineage_edges``'s direct
output (CA-46-W03); a KG-node-id round trip (CA-46-W05); and that the reconcile
tool refuses with the SAME shape (``EgeriaWriteDisabled``) as every other
write-gated tool in this package when ``EGERIA_ENABLE_WRITE`` is unset/false.
"""

from __future__ import annotations

import pytest

from egeria_mcp.lineage_scan import catalog_lineage_edges
from egeria_mcp.reconcile import (
    MalformedDatasetName,
    parse_iceberg_dataset_name,
    reconcile_openlineage_asset,
)

# egeria_asset_for_kg_node's round-trip tests live in test_asset_for_kg_node.py —
# egeria_mcp.kg_ingest (which it needs) transitively requires the certified
# epistemic_graph.numeric native kernel wheel, which is not importable in every
# environment (pre-existing: tests/test_kg_ingest.py hits the identical
# ImportError at collection); keeping that dependency isolated to its own file
# means it alone skips there, rather than this whole file's collection failing.

_GOOD_DATASET = "iceberg://lakehouse/sales/orders@snap-42"
_UPSTREAM_DATASET = "iceberg://lakehouse/raw/orders_raw@snap-7"


class FakeEgeriaApi:
    """Records create_asset/assert_lineage calls; idempotent by qualifiedName."""

    def __init__(self) -> None:
        self._assets: dict[str, str] = {}
        self._edges: dict[str, set[str]] = {}
        self._next = 0
        self.create_calls: list[str] = []
        self.assert_lineage_calls: list[tuple[str, str, str]] = []

    def _new_guid(self) -> str:
        self._next += 1
        return f"guid-{self._next}"

    def create_asset(self, type_name, qualified_name, display_name, **kw):
        self.create_calls.append(qualified_name)
        if qualified_name in self._assets:
            return {"guid": self._assets[qualified_name], "reused": True}
        guid = self._new_guid()
        self._assets[qualified_name] = guid
        return {"guid": guid, "reused": False}

    def find_asset(self, qualified_name):
        return self._assets.get(qualified_name)

    def lineage(self, guid, direction="both", depth=2):
        edges = self._edges.get(guid, set())
        return {
            "lineageLinkage": [
                {
                    "relatedElement": {"elementHeader": {"guid": g}},
                    "relatedElementAtEnd1": False,
                }
                for g in edges
            ]
        }

    def assert_lineage(self, source_guid, process_guid, target_guid):
        self.assert_lineage_calls.append((source_guid, process_guid, target_guid))
        self._edges.setdefault(source_guid, set()).add(process_guid)
        self._edges.setdefault(process_guid, set()).add(target_guid)
        return {"edges": [{"guid": "e1"}, {"guid": "e2"}]}

    def get_element(self, guid):
        for qn, g in self._assets.items():
            if g == guid:
                return {"qualifiedName": qn}
        return {}


# ── dataset-name parsing ──────────────────────────────────────────────────
def test_parse_iceberg_dataset_name():
    parts = parse_iceberg_dataset_name(_GOOD_DATASET)
    assert parts == {
        "catalog": "lakehouse",
        "namespace": "sales",
        "table": "orders",
        "snapshot": "snap-42",
    }


def test_parse_iceberg_dataset_name_malformed():
    with pytest.raises(MalformedDatasetName):
        parse_iceberg_dataset_name("s3://not-iceberg/orders")


# ── egeria_reconcile_openlineage_asset (CA-46-W04) ────────────────────────
def test_reconcile_fresh_dataset_creates_asset():
    api = FakeEgeriaApi()
    res = reconcile_openlineage_asset(api, _GOOD_DATASET)
    assert res["dataset_name"] == _GOOD_DATASET
    assert res["guid"] == "guid-1"
    assert res["reused"] is False
    assert "error" not in res
    assert api.create_calls == [_GOOD_DATASET]


def test_reconcile_idempotent_rerun_no_duplicate_asset():
    api = FakeEgeriaApi()
    first = reconcile_openlineage_asset(api, _GOOD_DATASET)
    second = reconcile_openlineage_asset(api, _GOOD_DATASET)
    assert first["guid"] == second["guid"]
    assert second["reused"] is True
    assert len(api._assets) == 1  # noqa: SLF001 — internal state check


def test_reconcile_idempotent_rerun_no_duplicate_lineage_edge():
    api = FakeEgeriaApi()
    reconcile_openlineage_asset(
        api, _GOOD_DATASET, job_name="etl-orders", produced_from=_UPSTREAM_DATASET
    )
    reconcile_openlineage_asset(
        api, _GOOD_DATASET, job_name="etl-orders", produced_from=_UPSTREAM_DATASET
    )
    # Only one real assert_lineage call reached the client; the rerun found the
    # edge already there and reused it.
    assert len(api.assert_lineage_calls) == 1


def test_reconcile_malformed_namespace_quarantines_never_guesses():
    api = FakeEgeriaApi()
    with pytest.raises(MalformedDatasetName):
        reconcile_openlineage_asset(api, "not-a-valid-name")
    assert api.create_calls == []  # never created a guessed asset


def test_reconcile_malformed_produced_from_quarantines():
    api = FakeEgeriaApi()
    with pytest.raises(MalformedDatasetName):
        reconcile_openlineage_asset(
            api, _GOOD_DATASET, job_name="etl-orders", produced_from="not-a-valid-name"
        )


def test_reconcile_write_disabled_same_refusal_shape_as_other_write_tools():
    """EGERIA_ENABLE_WRITE unset/false → EgeriaWriteDisabled, same as e.g. classify()."""
    from egeria_mcp.api.api_client_egeria import EgeriaApi, EgeriaWriteDisabled

    api = EgeriaApi(user_id="u", user_pwd="p", enable_write=False)
    with pytest.raises(EgeriaWriteDisabled):
        reconcile_openlineage_asset(api, _GOOD_DATASET)


def test_reconcile_tool_quarantine_shape(monkeypatch):
    """The MCP tool wrapper turns MalformedDatasetName into a typed quarantine dict.

    Quarantine happens before any Egeria call, but the tool still resolves the
    client eagerly (matching every sibling tool's ``get_client()`` call
    convention) — mock it so this test exercises only the quarantine path.
    """
    import asyncio

    import egeria_mcp.mcp.mcp_egeria as mcp_egeria_mod
    from egeria_mcp.mcp_server import get_mcp_instance

    monkeypatch.setattr(mcp_egeria_mod, "get_client", lambda: object())

    async def run():
        mcp, _args, _mw = get_mcp_instance(command_args=[])
        tool = await mcp.get_tool("egeria_reconcile_openlineage_asset")
        return await tool.fn(dataset_name="bogus")

    res = asyncio.new_event_loop().run_until_complete(run())
    assert res["quarantined"] is True
    assert res["reason"] == "malformed_dataset_name"


# ── egeria_lineage_scan (CA-46-W03) ───────────────────────────────────────
class _R:
    status_code = 200


class ScanFakeApi:
    """One asset under the first hub prefix, with one lineage edge — real data,
    no network — to prove the promoted tool returns EXACTLY what the internal
    helper returns, not a re-implementation."""

    def __init__(self) -> None:
        self._served = False

    def _bearer(self):
        return "tok"

    def _omvs(self, service, sub_path):
        return f"https://unreachable.invalid/{service}/{sub_path}"

    def _http(self):
        return self

    def post(self, url, headers=None, content=None):
        return _R()

    def _elements(self, resp):
        if self._served:
            return []
        self._served = True
        return [{"guid": "g1", "qualifiedName": "Node::foo", "typeName": "T"}]

    def lineage(self, guid, direction="both", depth=2):
        return {
            "lineageLinkage": [
                {
                    "relatedElement": {
                        "elementHeader": {"guid": "g2", "type": {"typeName": "T2"}},
                        "properties": {"qualifiedName": "Dataset::bar"},
                    },
                    "relatedElementAtEnd1": False,
                    "relationshipProperties": {"label": "flow"},
                }
            ]
        }


def test_lineage_scan_matches_catalog_lineage_edges_directly(monkeypatch):
    direct = catalog_lineage_edges(ScanFakeApi(), max_total=5)
    assert direct == [
        {
            "source": "g1",
            "target": "g2",
            "label": "flow",
            "sourceName": "Node::foo",
            "targetName": "Dataset::bar",
            "sourceType": "T",
            "targetType": "T2",
        }
    ]

    import asyncio

    import egeria_mcp.mcp.mcp_egeria as mcp_egeria_mod
    from egeria_mcp.mcp_server import get_mcp_instance

    monkeypatch.setattr(mcp_egeria_mod, "get_client", lambda: ScanFakeApi())

    async def run():
        mcp, _args, _mw = get_mcp_instance(command_args=[])
        tool = await mcp.get_tool("egeria_lineage_scan")
        return await tool.fn(max_total=5)

    via_tool = asyncio.new_event_loop().run_until_complete(run())
    assert via_tool == direct
