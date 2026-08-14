"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``egeria_mcp.kg_ingest`` seam with a fake engine client (no
engine required): the txn add_node/commit + edge calls, the Egeria record →
:GlossaryTerm/:GovernanceRule/:DataAsset mappings, the DataFlow → :flowsTo lineage
edges, and the full ``ingest_catalog`` orchestration over a fake client.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from typing import Any

import msgpack
import pytest
from agent_utilities.knowledge_graph.memory.native_ingest import NativeIngestError
from agent_utilities.security.brain_context import ActorContext, use_actor
from agent_utilities.models.company_brain import ActorType
from agent_utilities.knowledge_graph.core.session import GraphSession, use_session

from egeria_mcp.kg_ingest import (
    ingest_catalog,
    ingest_documents,
    ingest_entities,
    map_assets,
    map_glossary_terms,
    map_governance,
    map_lineage,
)


@pytest.fixture(autouse=True)
def _governed_session():
    actor = ActorContext(
        actor_id="subject:opaque:synthetic",
        actor_type=ActorType.AUTOMATED_SERVICE,
        roles=(),
        tenant_id="tenant:opaque:synthetic",
        authenticated=True,
    )
    session = GraphSession(
        actor=actor,
        tenant=actor.tenant_id,
        scopes=frozenset({"kg:write"}),
        graph="graph:opaque:synthetic",
        policy_version="policy:opaque:synthetic",
        audience="epistemic-graph",
    )
    with use_actor(actor), use_session(session):
        yield


class _FakeNodes:
    def __init__(self) -> None:
        self.values: dict[str, dict[str, Any]] = {}

    def properties(self, node_id: str) -> dict[str, Any] | None:
        return self.values.get(node_id)

    def list(self) -> list[tuple[str, dict[str, Any]]]:
        return list(self.values.items())


class _FakeChanges:
    def __init__(self, nodes: _FakeNodes) -> None:
        self.nodes = nodes
        self.edges: list[tuple[str, str, dict[str, Any]]] = []
        self.applied: list[dict[str, Any]] = []
        self.records: dict[str, dict[str, Any]] = {}
        self.versions: dict[str, dict[str, Any]] = {}

    def get(self, envelope_id: str) -> dict[str, Any] | None:
        return self.records.get(envelope_id)

    def content_version(self, object_id: str) -> dict[str, Any] | None:
        return self.versions.get(object_id)

    def cursor(self, _source: str, _partition: str = "") -> None:
        return None

    def apply(self, envelope: dict[str, Any]) -> dict[str, Any]:
        self.applied.append(envelope)
        mutation = envelope["mutation"]
        for operation in mutation["operations"]:
            method = operation["method"]
            params = method["params"]
            properties = msgpack.unpackb(params["properties_msgpack"], raw=False)
            if method["method"] == "AddNode":
                self.nodes.values[params["node_id"]] = properties
            elif method["method"] == "AddEdge":
                self.edges.append(
                    (params["source_id"], params["target_id"], properties)
                )
        version = envelope["content_version"]
        self.versions[version["object_id"]] = version
        self.records[envelope["envelope_id"]] = envelope
        return {
            "batch_id": mutation["batch_id"],
            "replayed": False,
            "projection_pending": False,
        }


class _FakeRdf:
    def validate_shacl(self, _shapes: str, _data_graph: str) -> dict[str, Any]:
        return {"conforms": True, "results": []}


class _FakeClient:
    def __init__(self) -> None:
        self.nodes = _FakeNodes()
        self.changes = _FakeChanges(self.nodes)
        self.rdf = _FakeRdf()

    @staticmethod
    def supports(operation: str) -> bool:
        return operation == "ApplyChangeEnvelope"


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
                "node_type": "GlossaryTerm",
                "name": "Customer",
            },
            {
                "id": "egeria:DataAsset:a1",
                "node_type": "DataAsset",
                "name": "CustomerDB",
            },
        ],
        [
            {
                "source": "egeria:DataAsset:a1",
                "target": "egeria:DataAsset:a2",
                "relationship": "flowsTo",
            }
        ],
        client=c,
    )
    assert res == {"nodes": 2, "edges": 1}
    assert len(c.changes.applied) == 1
    # provenance is stamped
    assert c.nodes.values["egeria:GlossaryTerm:t1"]["source"] == "egeria-mcp"
    assert c.nodes.values["egeria:GlossaryTerm:t1"]["domain"] == "egeria"
    assert c.changes.edges == [
        ("egeria:DataAsset:a1", "egeria:DataAsset:a2", {"relationship": "flowsTo"})
    ]


def test_ingest_documents_marks_document_type():
    c = _FakeClient()
    res = ingest_documents(
        [{"id": "egeria:GlossaryTerm:t1:def", "text": "Customer: buyer."}],
        client=c,
    )
    assert res == {"nodes": 1, "edges": 0}
    node = c.nodes.values["egeria:GlossaryTerm:t1:def"]
    assert node["node_type"] == "Document"
    assert node["text"] == "Customer: buyer."
    assert node["created_at"]


# ── mappers ──────────────────────────────────────────────────────────────────
def test_map_glossary_terms():
    ents, docs = map_glossary_terms(
        [{"guid": "t1", "displayName": "Customer", "summary": "A buyer."}]
    )
    assert ents[0]["id"] == "egeria:GlossaryTerm:t1"
    assert ents[0]["node_type"] == "GlossaryTerm"
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
    assert ents[0]["node_type"] == "GovernanceRule"
    assert docs[0]["doc_type"] == "governance_rule"


def test_map_assets_and_lineage():
    assets = map_assets([{"guid": "a1", "displayName": "DB", "typeName": "Database"}])
    assert assets[0]["id"] == "egeria:DataAsset:a1"
    assert assets[0]["node_type"] == "DataAsset"

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
            "relationship": "flowsTo",
        }
    ]


# ── orchestration ────────────────────────────────────────────────────────────
def test_ingest_catalog_over_fake_api():
    c = _FakeClient()
    res = ingest_catalog(_FakeApi(), client=c)
    # 1 term + 1 category + 1 gov + 2 assets + 2 lineage endpoints = 7 nodes
    assert res["nodes"] == 7
    assert res["edges"] == 1
    # 1 term def + 1 gov def = 2 documents
    assert res["documents"] == 2
    assert "egeria:GlossaryTerm:t1" in c.nodes.values
    assert "egeria:GovernanceRule:g1" in c.nodes.values
    assert "egeria:DataAsset:a1" in c.nodes.values


# ── guards ───────────────────────────────────────────────────────────────────
def test_ingest_rejects_legacy_structural_fields():
    with pytest.raises(NativeIngestError, match="canonical node_type"):
        ingest_entities([{"id": "legacy", "type": "Legacy"}], client=_FakeClient())


def test_ingest_empty_is_rejected():
    with pytest.raises(NativeIngestError, match="at least one entity"):
        ingest_entities([], client=_FakeClient())
