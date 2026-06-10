"""Bottom-up harvest connectors that populate Egeria *from* the data estate.

Egeria is the metadata/governance/lineage system-of-record; these connectors are the
write side of the federation — each reads a source system and catalogs it into Egeria
as governed assets (with confidentiality + lineage). Every connector is config-driven
(reads its connection from the environment) and **tolerant**: an unconfigured or
unreachable source reports ``skipped`` rather than raising, so the unified runner
(:func:`egeria_mcp.harvest.runner.harvest_all`) runs whatever is wired.
"""

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

__all__ = [
    "harvest_datastores",
    "harvest_processes",
    "harvest_erpnext",
    "harvest_repositories",
    "harvest_github",
    "harvest_containers",
    "harvest_servicenow",
    "harvest_identity",
    "harvest_finance",
    "harvest_projects",
    "harvest_archimate",
    "harvest_kafka",
    "harvest_crm",
    "harvest_leanix",
    "harvest_automation",
    "harvest_secrets",
    "harvest_documentdb",
    "harvest_files",
    "harvest_knowledge",
    "harvest_dns",
    "harvest_proxy",
    "harvest_m365",
    "harvest_vectors",
    "harvest_hosts",
    "harvest_markets",
    "harvest_semantic",
    "harvest_mailing",
    "harvest_iot",
    "harvest_ml",
    "harvest_chat",
    "harvest_observability",
    "harvest_monitoring",
    "harvest_archive",
    "harvest_llmops",
    "harvest_aris",
    "harvest_archer",
    "harvest_odoo",
]
