"""CA-46-W05: egeria_asset_for_kg_node — KG node id -> Egeria GUID round trip.

Split out from test_lineage_reconcile.py because ``egeria_mcp.kg_ingest``
(needed for ``asset_for_kg_node``) transitively imports
``agent_utilities.knowledge_graph.memory.native_ingest``, which requires the
certified ``epistemic_graph.numeric`` native kernel wheel — not importable in
every environment (pre-existing: ``tests/test_kg_ingest.py`` hits the identical
``ImportError`` at collection). Isolating the dependency here means only these
tests skip when it's missing, not the whole reconcile/scan test suite.
"""

from __future__ import annotations

import pytest

kg_ingest = pytest.importorskip(
    "egeria_mcp.kg_ingest",
    reason=(
        "agent_utilities.numeric requires the epistemic_graph native numeric "
        "kernel wheel, not importable in this environment"
    ),
    exc_type=ImportError,  # the kernel gap raises ImportError, not ModuleNotFoundError
)
asset_for_kg_node = kg_ingest.asset_for_kg_node

_GOOD_DATASET = "iceberg://lakehouse/sales/orders@snap-42"


class FakeEgeriaApi:
    def __init__(self) -> None:
        self._assets: dict[str, str] = {}
        self._next = 0

    def create_asset(self, type_name, qualified_name, display_name, **kw):
        if qualified_name in self._assets:
            return {"guid": self._assets[qualified_name], "reused": True}
        self._next += 1
        guid = f"guid-{self._next}"
        self._assets[qualified_name] = guid
        return {"guid": guid, "reused": False}

    def find_asset(self, qualified_name):
        return self._assets.get(qualified_name)

    def get_element(self, guid):
        for qn, g in self._assets.items():
            if g == guid:
                return {"qualifiedName": qn}
        return {}


def test_asset_for_kg_node_round_trip_egeria_domain():
    api = FakeEgeriaApi()
    created = api.create_asset("RelationalTable", _GOOD_DATASET, "orders@snap-42")
    guid = created["guid"]
    node_id = f"egeria:DataAsset:{guid}"
    res = asset_for_kg_node(api, node_id)
    assert res["guid"] == guid
    assert res["qualifiedName"] == _GOOD_DATASET


def test_asset_for_kg_node_round_trip_qualified_name_domain():
    api = FakeEgeriaApi()
    created = api.create_asset("RelationalTable", _GOOD_DATASET, "orders@snap-42")
    node_id = f"au:IcebergTable:{_GOOD_DATASET}"
    res = asset_for_kg_node(api, node_id)
    assert res["guid"] == created["guid"]
    assert res["qualifiedName"] == _GOOD_DATASET


def test_asset_for_kg_node_not_found():
    api = FakeEgeriaApi()
    res = asset_for_kg_node(api, "au:IcebergTable:iceberg://nope/nope/nope@0")
    assert res["error"] == "not_found"
    assert res["guid"] is None


def test_asset_for_kg_node_malformed():
    api = FakeEgeriaApi()
    res = asset_for_kg_node(api, "not-enough-parts")
    assert res["error"] == "malformed_node_id"
