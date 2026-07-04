"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``egeria_mcp.kg_ingest`` seam with a fake engine client (no
engine required): the txn add_node/commit + edge calls, the Egeria record →
:GlossaryTerm/:GovernanceRule/:DataAsset mappings, the DataFlow → :flowsTo lineage
edges, and the full ``ingest_catalog`` orchestration over a fake client.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from egeria_mcp.kg_ingest import (
    ingest_catalog,
    ingest_documents,
    ingest_entities,
    map_assets,
    map_glossary_terms,
    map_governance,
    map_lineage,
)


class _FakeTxn:
    def __init__(self):
        self.nodes = {}
        self.committed = False

    def begin(self, graph=None):
        self.graph = graph
        return "txn-1"

    def add_node(self, txn, node_id, props):
        self.nodes[node_id] = props

    def commit(self, txn):
        self.committed = True
        return True


class _FakeEdges:
    def __init__(self):
        self.edges = []

    def add(self, src, dst, props):
        self.edges.append((src, dst, props))


class _FakeClient:
    def __init__(self):
        self.txn = _FakeTxn()
        self.edges = _FakeEdges()


class _FakeApi:
    """Minimal EgeriaApi stand-in returning canned catalog records."""

    def list_glossary_terms(self):
        return [
            {
                "guid": "t1",
                "displayName": "Customer",
                "qualifiedName": "glossary/Customer",
                "summary": "A person or org that buys.",
            }
        ]

    def list_glossary_categories(self):
        return [
            {"guid": "c1", "displayName": "Parties", "qualifiedName": "cat/Parties"}
        ]

    def list_governance_definitions(self):
        return [
            {
                "guid": "g1",
                "displayName": "PII Retention",
                "qualifiedName": "gov/PIIRetention",
                "summary": "Retain PII for 7 years.",
                "typeName": "GovernancePolicy",
            }
        ]

    def list_assets(self):
        return [
            {"guid": "a1", "displayName": "CustomerDB", "typeName": "Database"},
            {"guid": "a2", "displayName": "SalesTable", "typeName": "RelationalTable"},
        ]

    def list_data_flows(self):
        return [
            {
                "source": "a1",
                "target": "a2",
                "label": "ETL",
                "sourceName": "CustomerDB",
                "targetName": "SalesTable",
            }
        ]


# ── low-level write seam ─────────────────────────────────────────────────────
def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {
                "id": "egeria:GlossaryTerm:t1",
                "type": "GlossaryTerm",
                "name": "Customer",
            },
            {"id": "egeria:DataAsset:a1", "type": "DataAsset", "name": "CustomerDB"},
        ],
        [
            {
                "source": "egeria:DataAsset:a1",
                "target": "egeria:DataAsset:a2",
                "type": "flowsTo",
            }
        ],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.txn.committed is True
    # provenance is stamped
    assert c.txn.nodes["egeria:GlossaryTerm:t1"]["source"] == "egeria-mcp"
    assert c.txn.nodes["egeria:GlossaryTerm:t1"]["domain"] == "egeria"
    assert c.edges.edges == [
        ("egeria:DataAsset:a1", "egeria:DataAsset:a2", {"type": "flowsTo"})
    ]


def test_ingest_documents_marks_document_type():
    c = _FakeClient()
    res = ingest_documents(
        [{"id": "egeria:GlossaryTerm:t1:def", "text": "Customer: buyer."}],
        client=c,
    )
    assert res == {"nodes": 1, "edges": 0}
    node = c.txn.nodes["egeria:GlossaryTerm:t1:def"]
    assert node["type"] == "Document"
    assert node["text"] == "Customer: buyer."
    assert node["created_at"]


# ── mappers ──────────────────────────────────────────────────────────────────
def test_map_glossary_terms():
    ents, docs = map_glossary_terms(
        [{"guid": "t1", "displayName": "Customer", "summary": "A buyer."}]
    )
    assert ents[0]["id"] == "egeria:GlossaryTerm:t1"
    assert ents[0]["type"] == "GlossaryTerm"
    assert ents[0]["externalToolId"] == "t1"
    assert docs[0]["id"] == "egeria:GlossaryTerm:t1:def"
    assert docs[0]["text"] == "Customer: A buyer."


def test_map_governance():
    ents, docs = map_governance(
        [
            {
                "guid": "g1",
                "displayName": "PII",
                "summary": "keep 7y",
                "typeName": "GovernancePolicy",
            }
        ]
    )
    assert ents[0]["id"] == "egeria:GovernanceRule:g1"
    assert ents[0]["type"] == "GovernanceRule"
    assert docs[0]["doc_type"] == "governance_rule"


def test_map_assets_and_lineage():
    assets = map_assets([{"guid": "a1", "displayName": "DB", "typeName": "Database"}])
    assert assets[0]["id"] == "egeria:DataAsset:a1"
    assert assets[0]["type"] == "DataAsset"

    endpoints, rels = map_lineage(
        [{"source": "a1", "target": "a2", "sourceName": "DB", "targetName": "T"}]
    )
    assert {e["id"] for e in endpoints} == {
        "egeria:DataAsset:a1",
        "egeria:DataAsset:a2",
    }
    assert rels == [
        {
            "source": "egeria:DataAsset:a1",
            "target": "egeria:DataAsset:a2",
            "type": "flowsTo",
        }
    ]


# ── orchestration ────────────────────────────────────────────────────────────
def test_ingest_catalog_over_fake_api():
    c = _FakeClient()
    res = ingest_catalog(_FakeApi(), client=c, graph="__commons__")
    # 1 term + 1 category + 1 gov + 2 assets + 2 lineage endpoints = 7 nodes
    assert res["nodes"] == 7
    assert res["edges"] == 1
    # 1 term def + 1 gov def = 2 documents
    assert res["documents"] == 2
    assert "egeria:GlossaryTerm:t1" in c.txn.nodes
    assert "egeria:GovernanceRule:g1" in c.txn.nodes
    assert "egeria:DataAsset:a1" in c.txn.nodes


# ── guards ───────────────────────────────────────────────────────────────────
def test_ingest_noops_without_engine():
    assert ingest_entities([{"id": "x", "type": "DataAsset"}]) is None


def test_ingest_empty_is_noop():
    assert ingest_entities([], client=_FakeClient()) is None
    assert ingest_documents([], client=_FakeClient()) is None
