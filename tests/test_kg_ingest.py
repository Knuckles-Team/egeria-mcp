"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``egeria_mcp.kg_ingest`` seam against a fake SDK transport (no
engine required): the ``agent_connector_sdk.ingest`` request/receipt shape, the
Egeria record → :GlossaryTerm/:GovernanceRule/:DataAsset mappings, the DataFlow →
:flowsTo lineage edges, and the full ``ingest_catalog`` orchestration.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from agent_connector_sdk.ingest import IngestError, KnowledgeIngest

from egeria_mcp.kg_ingest import (
    ingest_catalog,
    ingest_documents,
    ingest_entities,
    map_assets,
    map_glossary_terms,
    map_governance,
    map_lineage,
)


class _FakeTransport:
    def __init__(self) -> None:
        self.requests: list[Any] = []

    async def source_status(self, connector: str, stream: str) -> Any:
        return SimpleNamespace(accepted_checkpoint=None)

    async def submit(self, request: Any) -> Any:
        self.requests.append(request)
        return SimpleNamespace(
            affected_count=len(request.records),
            relationship_count=len(request.relationships),
        )

    async def store_blob(self, data: Any) -> Any:
        raise AssertionError("this connector's ingestion carries no media")


@pytest.fixture
def ingest():
    transport = _FakeTransport()
    return KnowledgeIngest(transport, loop=None), transport


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
async def test_ingest_entities_writes_nodes_and_edges(ingest):
    service, transport = ingest
    res = await ingest_entities(
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
        ingest=service,
    )
    assert res == {"nodes": 2, "edges": 1}
    assert len(transport.requests) == 1
    record_ids = {r.record_id for r in transport.requests[0].records}
    assert record_ids == {"egeria:GlossaryTerm:t1", "egeria:DataAsset:a1"}
    rel = transport.requests[0].relationships[0]
    assert rel.source.record_id == "egeria:DataAsset:a1"
    assert rel.target.record_id == "egeria:DataAsset:a2"


async def test_ingest_documents_marks_document_type(ingest):
    service, transport = ingest
    res = await ingest_documents(
        [{"id": "egeria:GlossaryTerm:t1:def", "text": "Customer: buyer."}],
        ingest=service,
    )
    assert res == {"nodes": 1, "edges": 0}
    record = transport.requests[0].records[0]
    assert record.record_id == "egeria:GlossaryTerm:t1:def"
    assert record.payload["text"] == "Customer: buyer."


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
async def test_ingest_catalog_over_fake_api(ingest):
    service, _transport = ingest
    res = await ingest_catalog(_FakeApi(), ingest=service)
    # 1 term + 1 category + 1 gov + 2 assets; the 2 lineage endpoints re-reference
    # the same 2 assets by id and are deduped (duplicate auxiliary node ids are
    # dropped) = 5 unique nodes.
    assert res["nodes"] == 5
    assert res["edges"] == 1
    # 1 term def + 1 gov def = 2 documents
    assert res["documents"] == 2


# ── guards ───────────────────────────────────────────────────────────────────
async def test_ingest_rejects_legacy_structural_fields(ingest):
    service, _transport = ingest
    with pytest.raises(IngestError):
        await ingest_entities([{"id": "legacy", "type": "Legacy"}], ingest=service)


async def test_ingest_empty_is_rejected(ingest):
    service, _transport = ingest
    with pytest.raises(IngestError, match="at least one entity"):
        await ingest_entities([], ingest=service)
