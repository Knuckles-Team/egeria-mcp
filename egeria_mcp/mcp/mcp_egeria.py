"""Thin MCP wrappers around the Egeria API client.

Each tool is a thin shim: it parses params, calls the matching
:class:`~egeria_mcp.api.api_client_egeria.EgeriaApi` method, and returns the
result. These are the *granular, typed* tools a policy router calls (lineage,
glossary, asset, governance reads; write tools gated by ``EGERIA_ENABLE_WRITE``) —
complementary to the official Dr.Egeria command/report MCP server. All API surface
lives in ``egeria_mcp.api`` — these tools add no business logic.
"""

import json
from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from egeria_mcp.auth import get_client


def _p(params_json: str) -> dict[str, Any]:
    return json.loads(params_json) if params_json else {}


def register_egeria_tools(mcp: FastMCP) -> None:
    """Register Egeria open-metadata / glossary / lineage / governance tools.

    CONCEPT:EA-KG.maintenance.broad-omvs-coverage-action — Broad OMVS Coverage. Action-dispatch tools (``egeria_catalog``,
    ``egeria_data_design``, ``egeria_collection``, ``egeria_solution``,
    ``egeria_governance_catalog``, ``egeria_actors``, ``egeria_metadata``) span 11
    View Services without a tool per noun.
    """

    # ── Read tools ───────────────────────────────────────────────────────────
    @mcp.tool(tags={"asset"})
    async def egeria_asset_search(
        query: str = Field(
            default="*", description="Search string (Egeria find syntax; '*' = all)."
        ),
        type_filter: str = Field(
            default="",
            description="Optional Egeria typeName substring filter (e.g. 'Database').",
        ),
    ) -> Any:
        """Search the Egeria asset catalog; returns flat asset records with GUIDs."""
        return get_client().asset_search(query, type_filter)

    @mcp.tool(tags={"glossary"})
    async def egeria_glossary_lookup(
        term: str = Field(description="Glossary term to look up (Egeria find syntax)."),
        glossary: str = Field(
            default="", description="Optional glossary qualifiedName filter."
        ),
    ) -> Any:
        """Look up business glossary terms (definitions, categories, relationships)."""
        return get_client().glossary_lookup(term, glossary)

    @mcp.tool(tags={"glossary"})
    async def egeria_glossary_categories() -> Any:
        """List the glossary category tree."""
        return get_client().glossary_categories()

    @mcp.tool(tags={"lineage"})
    async def egeria_lineage(
        asset_guid: str = Field(description="Egeria asset GUID to trace lineage for."),
        direction: str = Field(
            default="both", description="'upstream', 'downstream', or 'both'."
        ),
        depth: int = Field(default=2, description="Lineage traversal depth."),
    ) -> Any:
        """Return the data-lineage graph (upstream/downstream assets + processes)."""
        return get_client().lineage(asset_guid, direction, depth)

    @mcp.tool(tags={"governance"})
    async def egeria_governance_for(
        element_guid: str = Field(
            description="GUID of the element to fetch governance for."
        ),
    ) -> Any:
        """Return governance definitions + classifications applying to an element.

        The load-bearing tool for policy-aware routing: returns classifications
        (e.g. Confidentiality, Retention) and the policies governing the element.
        """
        return get_client().governance_for(element_guid)

    @mcp.tool(tags={"governance"})
    async def egeria_list_policies(
        domain: str = Field(
            default="",
            description="Optional governance domain filter (e.g. 'data-privacy').",
        ),
    ) -> Any:
        """List Egeria governance policies/rules (optionally filtered by domain)."""
        return get_client().list_policies(domain)

    @mcp.tool(tags={"governance", "routing"})
    async def egeria_governed_route(
        asset_guid: str = Field(
            description="Egeria GUID of the data asset about to be acted on.",
        ),
    ) -> Any:
        """Policy-aware routing decision for acting on an Egeria-catalogued asset.

        The federation delivering value: consults Egeria governance classifications
        + downstream lineage and returns a decision (proceed / review /
        require_approval) the orchestrator/policy-router can enforce.
        """
        from egeria_mcp.governed_routing import governed_route

        return governed_route(get_client(), asset_guid)

    @mcp.tool(tags={"harvest", "write"})
    async def egeria_harvest(
        layer: str = Field(
            default="all",
            description="Harvest layer to run, or 'all'. See the source registry for names.",
        ),
    ) -> Any:
        """Run a bottom-up harvest layer (or 'all') into Egeria.

        Generic entry point over every source connector (hosts, datastores,
        containers, dns, proxy, documentdb, vectors, kafka, finance, crm, erpnext,
        files, identity, secrets, servicenow, knowledge, m365, archimate, leanix,
        automation, processes, projects, gitlab, github). Each layer is config-driven
        and skips gracefully when its source/credentials are absent. Requires
        EGERIA_ENABLE_WRITE=true.
        """
        from egeria_mcp.harvest.runner import LAYERS, harvest_all

        if layer and layer != "all" and layer not in LAYERS:
            return {"error": f"unknown layer '{layer}'", "valid_layers": sorted(LAYERS)}
        return harvest_all(get_client(), None if layer == "all" else [layer])

    @mcp.tool(tags={"harvest", "write"})
    async def egeria_reconcile() -> Any:
        """Cross-link the harvested layers into one connected lineage/governance graph.

        Scans the catalog and creates DataFlow edges between assets that refer to the
        same real thing or have a real dependency across layers (host→asset hosting,
        service↔store identity, dataset→store containment, ingress→service exposure,
        monitor→target, CMDB identity, access-control, glossary semantic assignment),
        and propagates confidentiality up hosting chains. Idempotent. Requires
        EGERIA_ENABLE_WRITE=true.
        """
        from egeria_mcp.reconcile import reconcile

        return reconcile(get_client())

    @mcp.tool(tags={"governance"})
    async def egeria_audit() -> Any:
        """Completeness audit: report unlinked 'island' assets + per-layer coverage.

        Shows which catalogued assets still have no lineage connections (what
        reconciliation/harvest is still missing), with a coverage percentage per
        layer. Read-only.
        """
        from egeria_mcp.audit import audit

        return audit(get_client())

    @mcp.tool(tags={"kg", "ingest"})
    async def egeria_ingest_catalog() -> Any:
        """Natively ingest the Egeria catalog into epistemic-graph as typed OWL nodes.

        Lists glossary terms, glossary categories, governance definitions, assets,
        and DataFlow lineage edges via the Egeria client and pushes them into the
        KG as ``:GlossaryTerm`` / ``:GovernanceRule`` / ``:DataAsset`` /
        ``:GlossaryCategory`` nodes, ``:flowsTo`` lineage edges, and definition
        ``:Document`` nodes. Best-effort: returns ``{"ingested": null}`` when no KG
        engine is reachable. Read-only against Egeria.
        CONCEPT:AU-KG.ingest.enterprise-source-extractor.
        """
        from egeria_mcp.kg_ingest import ingest_catalog

        return {"ingested": ingest_catalog(get_client())}

    # ── Broad OMVS coverage (action-dispatch domain tools) ───────────────────
    # Each tool fans an ``action`` out to the matching EgeriaApi find method,
    # keeping the catalogue browsable without a separate tool per noun.
    def _dispatch(actions: dict[str, str], action: str, query: str) -> Any:
        method = actions.get(action)
        if not method:
            return {
                "error": f"unknown action '{action}'",
                "valid_actions": sorted(actions),
            }
        return getattr(get_client(), method)(query)

    _CATALOG = {
        "data_assets": "find_data_assets",
        "connections": "find_connections",
        "connector_types": "find_connector_types",
        "endpoints": "find_endpoints",
        "infrastructure_assets": "find_infrastructure_assets",
        "technology_types": "find_technology_types",
        "schema_types": "find_schema_types",
        "schema_attributes": "find_schema_attributes",
    }

    @mcp.tool(tags={"asset"})
    async def egeria_catalog(
        action: str = Field(description=f"One of: {', '.join(sorted(_CATALOG))}."),
        query: str = Field(default="", description="Search string ('' = match-all)."),
    ) -> Any:
        """Browse the technical catalog: assets, connections, endpoints, schema."""
        return _dispatch(_CATALOG, action, query)

    _DATA_DESIGN = {
        "data_structures": "find_data_structures",
        "data_fields": "find_data_fields",
        "data_value_specifications": "find_data_value_specifications",
    }

    @mcp.tool(tags={"data-design"})
    async def egeria_data_design(
        action: str = Field(description=f"One of: {', '.join(sorted(_DATA_DESIGN))}."),
        query: str = Field(default="", description="Search string ('' = match-all)."),
    ) -> Any:
        """Browse data-designer artifacts: data structures, fields, value specs."""
        return _dispatch(_DATA_DESIGN, action, query)

    _COLLECTION = {
        "collections": "find_collections",
        "digital_products": "find_digital_products",
    }

    @mcp.tool(tags={"collection"})
    async def egeria_collection(
        action: str = Field(description=f"One of: {', '.join(sorted(_COLLECTION))}."),
        query: str = Field(default="", description="Search string ('' = match-all)."),
    ) -> Any:
        """Browse collections and digital products."""
        return _dispatch(_COLLECTION, action, query)

    _SOLUTION = {
        "information_supply_chains": "find_information_supply_chains",
        "solution_blueprints": "find_solution_blueprints",
        "solution_components": "find_solution_components",
    }

    @mcp.tool(tags={"solution-architecture"})
    async def egeria_solution(
        action: str = Field(description=f"One of: {', '.join(sorted(_SOLUTION))}."),
        query: str = Field(default="", description="Search string ('' = match-all)."),
    ) -> Any:
        """Browse solution architecture: supply chains, blueprints, components."""
        return _dispatch(_SOLUTION, action, query)

    _GOV_CATALOG = {
        "governance_definitions": "list_governance_definitions",
        "external_references": "find_external_references",
        "valid_values": "find_valid_values",
    }

    @mcp.tool(tags={"governance"})
    async def egeria_governance_catalog(
        action: str = Field(description=f"One of: {', '.join(sorted(_GOV_CATALOG))}."),
        query: str = Field(default="", description="Search string ('' = match-all)."),
    ) -> Any:
        """Browse governance definitions, external references, valid-value sets."""
        actions = _GOV_CATALOG
        method = actions.get(action)
        if not method:
            return {
                "error": f"unknown action '{action}'",
                "valid_actions": sorted(actions),
            }
        fn = getattr(get_client(), method)
        # list_governance_definitions takes no arg
        return fn() if action == "governance_definitions" else fn(query)

    _ACTORS = {
        "actor_profiles": "find_actor_profiles",
        "actor_roles": "find_actor_roles",
        "user_identities": "find_user_identities",
        "projects": "find_projects",
        "communities": "find_communities",
        "locations": "find_locations",
        "cohorts": "find_cohorts",
    }

    @mcp.tool(tags={"actor"})
    async def egeria_actors(
        action: str = Field(description=f"One of: {', '.join(sorted(_ACTORS))}."),
        query: str = Field(default="", description="Search string ('' = match-all)."),
    ) -> Any:
        """Browse people/teams, projects, communities, locations, cohorts."""
        return _dispatch(_ACTORS, action, query)

    @mcp.tool(tags={"metadata"})
    async def egeria_metadata(
        action: str = Field(
            description="'find' (search any element type) or 'get' (by GUID)."
        ),
        query: str = Field(
            default="", description="Search string for 'find', or a GUID for 'get'."
        ),
    ) -> Any:
        """Generic open-metadata access: search across all types, or get by GUID."""
        client = get_client()
        if action == "get":
            return client.get_element(query)
        if action == "find":
            return client.find_metadata_elements(query)
        return {"error": f"unknown action '{action}'", "valid_actions": ["find", "get"]}

    # ── Harvest tools (gated by EGERIA_ENABLE_WRITE) ─────────────────────────
    @mcp.tool(tags={"harvest", "write"})
    async def egeria_harvest_datastores() -> Any:
        """Catalog the data-store estate into Egeria (bottom-up harvest, anchor layer).

        Idempotently populates Egeria with the business-glossary backbone, the
        data-store servers + databases (with Confidentiality classifications), and
        the DataFlow lineage between them — the substrate every downstream harvest
        (ERPNext/Camunda/GitLab) references. Requires EGERIA_ENABLE_WRITE=true.
        """
        from egeria_mcp.harvest import harvest_datastores

        return harvest_datastores(get_client())

    @mcp.tool(tags={"harvest", "write"})
    async def egeria_harvest_processes() -> Any:
        """Catalog Camunda BPMN process definitions into Egeria (process layer).

        Reads process definitions live from the Camunda 7 engine (CAMUNDA7_URL /
        CAMUNDA_URL) and idempotently catalogs each as an Egeria Process asset.
        Requires EGERIA_ENABLE_WRITE=true.
        """
        from egeria_mcp.harvest import harvest_processes

        return harvest_processes(get_client())

    @mcp.tool(tags={"harvest", "write"})
    async def egeria_harvest_erpnext() -> Any:
        """Catalog ERPNext DocTypes into Egeria (ERP layer).

        Reads business-critical DocTypes live from ERPNext (ERPNEXT_URL +
        ERPNEXT_TOKEN) and catalogs each as an Egeria data asset with
        confidentiality by data kind. Requires EGERIA_ENABLE_WRITE=true.
        """
        from egeria_mcp.harvest import harvest_erpnext

        return harvest_erpnext(get_client())

    @mcp.tool(tags={"harvest", "write"})
    async def egeria_harvest_repositories() -> Any:
        """Catalog GitLab projects into Egeria (code/CI layer).

        Reads projects live from GitLab (GITLAB_URL + GITLAB_TOKEN) and catalogs
        each as an Egeria DeployedSoftwareComponent asset. Requires
        EGERIA_ENABLE_WRITE=true.
        """
        from egeria_mcp.harvest import harvest_repositories

        return harvest_repositories(get_client())

    @mcp.tool(tags={"harvest", "write"})
    async def egeria_harvest_github() -> Any:
        """Catalog GitHub repositories into Egeria (GITHUB_TOKEN [+ GITHUB_ORG])."""
        from egeria_mcp.harvest import harvest_github

        return harvest_github(get_client())

    @mcp.tool(tags={"harvest", "write"})
    async def egeria_harvest_containers() -> Any:
        """Catalog the Docker Swarm estate (nodes + services) into Egeria — the
        infrastructure substrate. Config: PORTAINER_URL + PORTAINER_API_KEY.
        Requires EGERIA_ENABLE_WRITE=true.
        """
        from egeria_mcp.harvest import harvest_containers

        return harvest_containers(get_client())

    @mcp.tool(tags={"harvest", "write"})
    async def egeria_harvest_servicenow() -> Any:
        """Catalog ServiceNow CMDB configuration items into Egeria.
        Config: SERVICENOW_URL + USER/PASSWORD (or TOKEN). Requires EGERIA_ENABLE_WRITE=true.
        """
        from egeria_mcp.harvest import harvest_servicenow

        return harvest_servicenow(get_client())

    @mcp.tool(tags={"harvest", "write"})
    async def egeria_harvest_identity() -> Any:
        """Catalog Keycloak realms (security domains) + clients (apps) into Egeria.
        Config: KEYCLOAK_URL + KEYCLOAK_TOKEN (or CLIENT_ID/SECRET). Requires EGERIA_ENABLE_WRITE=true.
        """
        from egeria_mcp.harvest import harvest_identity

        return harvest_identity(get_client())

    @mcp.tool(tags={"harvest", "write"})
    async def egeria_harvest_finance() -> Any:
        """Catalog Firefly-III accounts into Egeria (financial data assets).
        Config: FIREFLY_URL + FIREFLY_TOKEN. Requires EGERIA_ENABLE_WRITE=true.
        """
        from egeria_mcp.harvest import harvest_finance

        return harvest_finance(get_client())

    @mcp.tool(tags={"harvest", "write"})
    async def egeria_harvest_projects() -> Any:
        """Catalog Plane/Jira projects into Egeria as Projects.
        Config: PLANE_URL/TOKEN/WORKSPACE or JIRA_URL/USER/TOKEN. Requires EGERIA_ENABLE_WRITE=true.
        """
        from egeria_mcp.harvest import harvest_projects

        return harvest_projects(get_client())

    @mcp.tool(tags={"harvest", "write"})
    async def egeria_harvest_aris() -> Any:
        """Catalog ARIS models into Egeria — process models (BPM) + architecture
        models (enterprise-architecture). Config: ARIS_URL + ARIS_TOKEN (optional
        ARIS_API_PATH). Requires EGERIA_ENABLE_WRITE=true.
        """
        from egeria_mcp.harvest import harvest_aris

        return harvest_aris(get_client())

    @mcp.tool(tags={"harvest", "write"})
    async def egeria_harvest_archer() -> Any:
        """Catalog RSA Archer GRC records (risks/controls/findings) into Egeria.
        Config: ARCHER_URL + ARCHER_TOKEN (optional ARCHER_APPLICATIONS). Requires
        EGERIA_ENABLE_WRITE=true.
        """
        from egeria_mcp.harvest import harvest_archer

        return harvest_archer(get_client())

    @mcp.tool(tags={"harvest", "write"})
    async def egeria_harvest_crm() -> Any:
        """Catalog Twenty CRM companies + people into Egeria (crm cohort with Odoo).
        Config: TWENTY_URL + TWENTY_TOKEN (optional TWENTY_API_PREFIX, default
        '/rest'). Requires EGERIA_ENABLE_WRITE=true.
        """
        from egeria_mcp.harvest import harvest_crm

        return harvest_crm(get_client())

    @mcp.tool(tags={"harvest", "write"})
    async def egeria_harvest_odoo() -> Any:
        """Catalog Odoo CRM customers + leads into Egeria (crm cohort with Twenty).
        Config: ODOO_URL + ODOO_DB + ODOO_USER + ODOO_PASSWORD. Requires
        EGERIA_ENABLE_WRITE=true.
        """
        from egeria_mcp.harvest import harvest_odoo

        return harvest_odoo(get_client())

    # ── Write tools (gated by EGERIA_ENABLE_WRITE) ───────────────────────────
    @mcp.tool(tags={"governance", "write"})
    async def egeria_classify(
        element_guid: str = Field(description="GUID of the element to classify."),
        classification: str = Field(
            description="Classification typeName (e.g. 'Confidentiality')."
        ),
        properties_json: str = Field(
            default="{}", description="JSON properties for the classification."
        ),
    ) -> Any:
        """Apply a classification to an element (requires EGERIA_ENABLE_WRITE=true)."""
        return get_client().classify(element_guid, classification, _p(properties_json))

    @mcp.tool(tags={"glossary", "write"})
    async def egeria_create_term(
        glossary: str = Field(description="Target glossary GUID or qualifiedName."),
        name: str = Field(description="Term display name."),
        definition: str = Field(default="", description="Term definition / summary."),
    ) -> Any:
        """Create a glossary term (requires EGERIA_ENABLE_WRITE=true)."""
        return get_client().create_term(glossary, name, definition)

    @mcp.tool(tags={"lineage", "write"})
    async def egeria_assert_lineage(
        source_guid: str = Field(description="Source asset GUID."),
        process_guid: str = Field(description="Process GUID linking source to target."),
        target_guid: str = Field(description="Target asset GUID."),
    ) -> Any:
        """Assert a data-flow lineage edge (requires EGERIA_ENABLE_WRITE=true).

        Used for KG→Egeria provenance write-back: records that a run consumed
        ``source`` and produced ``target`` via ``process``.
        """
        return get_client().assert_lineage(source_guid, process_guid, target_guid)

    @mcp.tool(tags={"asset", "write"})
    async def egeria_create_asset(
        type_name: str = Field(
            description="Egeria asset type (e.g. 'SoftwareServer', 'RelationalDatabase')."
        ),
        qualified_name: str = Field(description="Unique qualifiedName for the asset."),
        display_name: str = Field(description="Human-readable display name."),
        description: str = Field(default="", description="Asset description."),
        deployed_implementation_type: str = Field(
            default="", description="e.g. 'PostgreSQL Server'."
        ),
        confidentiality_level: int = Field(
            default=-1, description="0–4 Confidentiality level (-1 = none)."
        ),
    ) -> Any:
        """Create a data asset, optionally classified (requires EGERIA_ENABLE_WRITE=true)."""
        return get_client().create_asset(
            type_name,
            qualified_name,
            display_name,
            description=description,
            deployed_implementation_type=deployed_implementation_type,
            confidentiality_level=None
            if confidentiality_level < 0
            else confidentiality_level,
        )

    @mcp.tool(tags={"collection", "write"})
    async def egeria_create_collection(
        display_name: str = Field(description="Collection display name."),
        description: str = Field(default="", description="Collection description."),
        category: str = Field(default="", description="Optional collectionType."),
    ) -> Any:
        """Create a collection / digital-product folder (requires EGERIA_ENABLE_WRITE=true)."""
        return get_client().create_collection(
            display_name, description, category=category
        )

    @mcp.tool(tags={"project", "write"})
    async def egeria_create_project(
        display_name: str = Field(description="Project name."),
        description: str = Field(default="", description="Project description."),
    ) -> Any:
        """Create a project (requires EGERIA_ENABLE_WRITE=true)."""
        return get_client().create_project(display_name, description)
