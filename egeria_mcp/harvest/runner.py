"""Run every configured harvest layer in bottom-up order.

Each layer is tolerant — one that is unconfigured/unreachable reports ``skipped``
rather than raising, so ``harvest_all`` runs whatever is wired and skips the rest.
"""

from __future__ import annotations

import os
from typing import Any

from egeria_mcp.harvest.archer import harvest_archer
from egeria_mcp.harvest.archimate import harvest_archimate
from egeria_mcp.harvest.archive import harvest_archive
from egeria_mcp.harvest.aris import harvest_aris
from egeria_mcp.harvest.automation import harvest_automation
from egeria_mcp.harvest.chat import harvest_chat
from egeria_mcp.harvest.containers import harvest_containers
from egeria_mcp.harvest.crm import harvest_crm
from egeria_mcp.harvest.datastores import harvest_datastores
from egeria_mcp.harvest.dns import harvest_dns
from egeria_mcp.harvest.documentdb import harvest_documentdb
from egeria_mcp.harvest.erpnext import harvest_erpnext
from egeria_mcp.harvest.files import harvest_files
from egeria_mcp.harvest.finance import harvest_finance
from egeria_mcp.harvest.hosts import harvest_hosts
from egeria_mcp.harvest.identity import harvest_identity
from egeria_mcp.harvest.iot import harvest_iot
from egeria_mcp.harvest.kafka import harvest_kafka
from egeria_mcp.harvest.knowledge import harvest_knowledge
from egeria_mcp.harvest.leanix import harvest_leanix
from egeria_mcp.harvest.llmops import harvest_llmops
from egeria_mcp.harvest.m365 import harvest_m365
from egeria_mcp.harvest.mailing import harvest_mailing
from egeria_mcp.harvest.markets import harvest_markets
from egeria_mcp.harvest.ml import harvest_ml
from egeria_mcp.harvest.monitoring import harvest_monitoring
from egeria_mcp.harvest.observability import harvest_observability
from egeria_mcp.harvest.odoo import harvest_odoo
from egeria_mcp.harvest.processes import harvest_processes
from egeria_mcp.harvest.projects import harvest_projects
from egeria_mcp.harvest.proxy import harvest_proxy
from egeria_mcp.harvest.repositories import harvest_github, harvest_repositories
from egeria_mcp.harvest.secrets import harvest_secrets
from egeria_mcp.harvest.semantic import harvest_semantic
from egeria_mcp.harvest.servicenow import harvest_servicenow
from egeria_mcp.harvest.vectors import harvest_vectors

# Bottom-up order: substrate (hosts, stores, swarm, network) → data/systems →
# architecture → code/work → collaboration/observability.
LAYERS: dict[str, Any] = {
    "hosts": harvest_hosts,
    "datastores": harvest_datastores,
    "containers": harvest_containers,
    "dns": harvest_dns,
    "proxy": harvest_proxy,
    "documentdb": harvest_documentdb,
    "vectors": harvest_vectors,
    "semantic": harvest_semantic,
    "kafka": harvest_kafka,
    "finance": harvest_finance,
    "markets": harvest_markets,
    "crm": harvest_crm,
    "odoo": harvest_odoo,
    "erpnext": harvest_erpnext,
    "mailing": harvest_mailing,
    "files": harvest_files,
    "ml": harvest_ml,
    "identity": harvest_identity,
    "secrets": harvest_secrets,
    "servicenow": harvest_servicenow,
    "archer": harvest_archer,
    "knowledge": harvest_knowledge,
    "m365": harvest_m365,
    "iot": harvest_iot,
    "archimate": harvest_archimate,
    "leanix": harvest_leanix,
    "aris": harvest_aris,
    "automation": harvest_automation,
    "processes": harvest_processes,
    "projects": harvest_projects,
    "gitlab": harvest_repositories,
    "github": harvest_github,
    "chat": harvest_chat,
    "observability": harvest_observability,
    "monitoring": harvest_monitoring,
    "archive": harvest_archive,
    "llmops": harvest_llmops,
}


def harvest_all(api: Any, layers: list[str] | None = None) -> dict[str, Any]:
    """Run all (or the named) harvest layers; return ``{layer: report}``.

    After harvesting sources into Egeria, natively mirror the resulting catalog
    (glossary terms, governance rules, assets, lineage) into the epistemic-graph
    KG as typed OWL nodes (CONCEPT:AU-KG.ingest.enterprise-source-extractor).
    Default-on; set ``EGERIA_KG_INGEST=false`` to skip. Best-effort: a missing KG
    engine no-ops without affecting the harvest report.
    """
    out: dict[str, Any] = {}
    for name, fn in LAYERS.items():
        if layers and name not in layers:
            continue
        try:
            out[name] = fn(api)
        except Exception as exc:  # never let one layer abort the rest
            out[name] = {"error": str(exc)}
    if os.getenv("EGERIA_KG_INGEST", "true").lower() not in ("false", "0", "no"):
        try:
            from egeria_mcp.kg_ingest import ingest_catalog

            out["_kg_ingest"] = ingest_catalog(api)
        except Exception as exc:  # never let KG ingest abort the harvest
            out["_kg_ingest"] = {"error": str(exc)}
    return out
