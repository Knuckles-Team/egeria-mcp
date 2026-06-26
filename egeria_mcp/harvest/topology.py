"""Declared data-store estate + business-glossary backbone (the harvest source).

This is the *substrate* layer of the bottom-up harvest: the data stores of a
deployment and the core business vocabulary that everything downstream references.
It is declared (not live-surveyed) because data stores commonly sit on an internal
network not reachable from where the harvest runs; a live Egeria PostgreSQL
integration connector enriches these same assets with table/column detail when run
inside that network. The assets, confidentiality assignments, and data flows
declared here are real once pointed at a real estate.

The built-in :data:`DEFAULT_TOPOLOGY` is a **generic, non-sensitive example**. Point
the harvest at your real estate with the ``EGERIA_HARVEST_TOPOLOGY`` environment
variable (path to a JSON file with the same shape) — keep that file outside any
public repository so internal hostnames/addresses are never published.

Confidentiality scale (Egeria ``Confidentiality`` levels): 0 Unclassified,
1 Internal, 2 Confidential, 3 Sensitive, 4 Restricted.
"""

from __future__ import annotations

import json
import os
from typing import Any

from agent_utilities.core.config import setting

# ── Business glossary backbone (the ``:Concept`` layer the KG federates) ──────
GLOSSARY: dict[str, str] = {
    "name": "Data Governance Glossary",
    "description": (
        "Business glossary backbone for the data estate — the authoritative "
        "vocabulary the knowledge graph and governed workflows reference."
    ),
}

TERMS: list[dict[str, str]] = [
    {
        "name": "Personal Data Record",
        "summary": "Identifiable record about a person.",
        "description": "PII/PHI-bearing record; gates handling under confidentiality controls.",
    },
    {
        "name": "Knowledge Graph",
        "summary": "The cognition/orchestration graph plane.",
        "description": "Capability/lineage graph; consumes Egeria glossary terms as concepts.",
    },
    {
        "name": "Metadata Collection",
        "summary": "A metadata repository's set of governed metadata.",
        "description": "The active-metadata-store holds the durable open-metadata collection.",
    },
    {
        "name": "Data Lineage",
        "summary": "The producer→consumer flow of data across stores and processes.",
        "description": "Modelled in Egeria as DataFlow relationships between assets.",
    },
    {
        "name": "Confidentiality Classification",
        "summary": "Governance classification setting an asset's confidentiality level.",
        "description": "Drives policy-aware routing: level >= Confidential requires approval.",
    },
    {
        "name": "Business Process",
        "summary": "A BPMN process consuming and producing governed datasets.",
        "description": "Reconciled with KG :BusinessProcess nodes during the process harvest.",
    },
    {
        "name": "Governance Policy",
        "summary": "A rule constraining how data assets may be used.",
        "description": "Egeria owns data-governance policy; the KG/ADR layer owns architecture governance.",
    },
]

# ── Generic example estate (override via EGERIA_HARVEST_TOPOLOGY) ──────────────
# ``key`` is an internal handle used to wire the lineage flows below.
STORES: list[dict[str, Any]] = [
    {
        "key": "operational-db",
        "name": "operational-db",
        "type_name": "SoftwareServer",
        "deployed_implementation_type": "PostgreSQL Server",
        "description": "Primary operational relational store.",
        "confidentiality_level": 2,
    },
    {
        "key": "metadata-db",
        "name": "metadata-db",
        "type_name": "SoftwareServer",
        "deployed_implementation_type": "PostgreSQL Server",
        "description": "Metadata repository host.",
        "confidentiality_level": 1,
    },
    {
        "key": "event-broker",
        "name": "event-broker",
        "type_name": "SoftwareServer",
        "deployed_implementation_type": "Apache Kafka Server",
        "description": "Event bus / ingestion stream.",
        "confidentiality_level": 1,
    },
]

DATASETS: list[dict[str, Any]] = [
    {
        "key": "operational-db.primary",
        "name": "primary",
        "type_name": "RelationalDatabase",
        "parent": "operational-db",
        "deployed_implementation_type": "PostgreSQL Relational Database",
        "description": "Primary operational database — business data.",
        "confidentiality_level": 2,
    },
    {
        "key": "metadata-db.metadata",
        "name": "metadata",
        "type_name": "RelationalDatabase",
        "parent": "metadata-db",
        "deployed_implementation_type": "PostgreSQL Relational Database",
        "description": "Metadata-store repository database.",
        "confidentiality_level": 1,
    },
]

FLOWS: list[dict[str, str]] = [
    {
        "source": "operational-db.primary",
        "target": "event-broker",
        "label": "change-events",
        "description": "Change events published to the event bus.",
    },
    {
        "source": "event-broker",
        "target": "metadata-db.metadata",
        "label": "persist",
        "description": "Events persisted into the metadata-store repository.",
    },
]

DEFAULT_TOPOLOGY: dict[str, Any] = {
    "glossary": GLOSSARY,
    "terms": TERMS,
    "stores": STORES,
    "datasets": DATASETS,
    "flows": FLOWS,
}


def load_topology() -> dict[str, Any]:
    """Return the harvest topology.

    If ``EGERIA_HARVEST_TOPOLOGY`` points at a readable JSON file, it is loaded and
    its top-level keys (``glossary``/``terms``/``stores``/``datasets``/``flows``)
    override the generic :data:`DEFAULT_TOPOLOGY`. Otherwise the built-in example is
    returned. Keep the override file out of any public repository.
    """
    path = setting("EGERIA_HARVEST_TOPOLOGY")
    topology = {
        k: list(v) if isinstance(v, list) else dict(v)
        for k, v in DEFAULT_TOPOLOGY.items()
    }
    if path and os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as fh:
                override = json.load(fh)
            if isinstance(override, dict):
                topology.update(
                    {k: v for k, v in override.items() if k in DEFAULT_TOPOLOGY}
                )
        except (OSError, ValueError):
            pass  # tolerant: fall back to the built-in example
    return topology
