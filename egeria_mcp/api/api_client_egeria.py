"""Raw-REST Egeria client facade (no pyegeria runtime dependency).

``EgeriaApi`` talks to the Apache Egeria OMAG platform's View Server (OMVS) REST
surface directly with ``httpx`` — a deliberate choice over the ``pyegeria`` client
because pyegeria 6.0.x's synchronous wrappers rely on ``asyncio.get_event_loop()``,
which **raises on Python 3.14** (no implicit loop), breaking every call. Plain
``httpx`` works identically on 3.11 and 3.14, so this facade is runtime-robust.

Endpoints (confirmed against Egeria 6.0):
* token  ``POST {platform}/api/token``  → bearer JWT (body ``{userId,password}``)
* OMVS   ``{platform}/servers/{view_server}/api/open-metadata/{service}/...``
* search ``.../{service}/.../by-search-string?startFrom&pageSize`` with a
  ``SearchStringRequestBody`` — note ``searchString`` is a **regex** (use ``.*``).

It exposes the normalized ``list_*`` methods the KG ``egeria`` extractor consumes
and the granular query/write methods the MCP tools call. Every call degrades to
``[]`` / a clear error rather than raising at import or on a transient failure.
"""

from __future__ import annotations

import json as _json
from typing import Any

from agent_utilities.core.transport_security import (
    ResolvedTLSProfile,
    resolve_tls_profile,
)

try:  # httpx is always present (agent-utilities dep); guard anyway
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False

# Back-compat flag some callers/tests import; REST path needs no pyegeria.
PYEGERIA_AVAILABLE = False


class EgeriaWriteDisabled(RuntimeError):
    """Raised when a write method is called but EGERIA_ENABLE_WRITE is false."""


_SEARCH_ALL = (
    ""  # Egeria by-search-string: EMPTY string = match-all (".*" matches nothing)
)


def _slug(name: str) -> str:
    """Stable qualifiedName fragment from a display name (deterministic)."""
    return "".join(ch if ch.isalnum() else "" for ch in name.strip().title())


def _norm(el: dict) -> dict:
    """Flatten an Egeria OMVS element envelope into a flat record."""
    if not isinstance(el, dict):
        return {}
    _header = el.get("elementHeader")
    header = _header if isinstance(_header, dict) else {}
    props = el.get("properties") or el.get("glossaryProperties") or {}
    if not isinstance(props, dict):
        props = {}
    _type_info = header.get("type")
    type_info = _type_info if isinstance(_type_info, dict) else {}
    flat: dict[str, Any] = {
        "guid": el.get("guid") or header.get("guid") or header.get("GUID"),
        "typeName": props.get("typeName")
        or type_info.get("typeName")
        or el.get("typeName"),
        "displayName": props.get("displayName") or props.get("name"),
        "qualifiedName": props.get("qualifiedName"),
        "summary": props.get("summary") or props.get("description"),
    }
    for k, v in props.items():
        flat.setdefault(k, v)
    # surface classifications (for governance/confidentiality props downstream)
    cls = header.get("classifications")
    if cls:
        flat["classifications"] = cls
    return {k: v for k, v in flat.items() if v is not None}


class EgeriaApi:
    """Tolerant raw-REST facade over Egeria's OMVS for the MCP tools + KG extractor.

    CONCEPT:EA-KG.compute.raw-rest-omvs-facade — Raw-REST OMVS Facade. A tolerant httpx client over the View
    Server; no ``pyegeria`` runtime dep (its ``asyncio.get_event_loop()`` raises on
    3.14). Every call degrades to ``[]`` / a clear error rather than raising.
    """

    def __init__(
        self,
        platform_url: str = "https://localhost:9443",
        view_server: str = "view-server",
        user_id: str | None = None,
        user_pwd: str | None = None,
        *,
        tls_profile: ResolvedTLSProfile | None = None,
        enable_write: bool = False,
        timeout: float = 30.0,
    ) -> None:
        self.platform_url = platform_url.rstrip("/")
        self.view_server = view_server
        if not user_id or not user_pwd:
            raise ValueError("Egeria user credentials are required")
        self.user_id = user_id
        self.user_pwd = user_pwd
        self.tls_profile = tls_profile or resolve_tls_profile("EGERIA")
        self.enable_write = enable_write
        self.timeout = timeout
        self._client: Any = None
        self._token: str | None = None

    # ── HTTP plumbing ────────────────────────────────────────────────────────
    def _http(self) -> Any:
        if self._client is None:
            if not HTTPX_AVAILABLE:
                raise RuntimeError("httpx is required for egeria-mcp.")
            self._client = httpx.Client(
                timeout=self.timeout,
                **self.tls_profile.httpx_kwargs(),
            )
        return self._client

    def _bearer(self) -> str:
        """Fetch (and cache) a bearer token from the platform token endpoint."""
        if self._token:
            return self._token
        r = self._http().post(
            f"{self.platform_url}/api/token",
            json={"userId": self.user_id, "password": self.user_pwd},
        )
        r.raise_for_status()
        self._token = r.text.strip()
        return self._token

    def _omvs(self, service: str, sub_path: str) -> str:
        return (
            f"{self.platform_url}/servers/{self.view_server}"
            f"/api/open-metadata/{service}/{sub_path.lstrip('/')}"
        )

    # OMVS find responses usually key the hits as ``elements``; a few view
    # services use a typed key (``elementList``/``element``) instead.
    _ELEMENT_KEYS = ("elements", "elementList", "element")

    def _elements(self, resp: Any) -> list[dict]:
        try:
            data = resp.json()
        except Exception:
            return []
        if not isinstance(data, dict):
            return []
        for key in self._ELEMENT_KEYS:
            els = data.get(key)
            if isinstance(els, list):
                return [_norm(e) for e in els]
            if isinstance(els, dict):  # single-element envelope
                return [_norm(els)]
        return []

    def _search(
        self,
        service: str,
        sub_path: str,
        search: str = _SEARCH_ALL,
        page_size: int = 100,
    ) -> list[dict]:
        """POST an OMVS by-search-string query, returning normalized records."""
        try:
            tok = self._bearer()
        except Exception:
            return []
        url = self._omvs(service, sub_path)
        # Egeria by-search-string: empty searchString = match-all; a non-empty value
        # is a contains/regex match. The startsWith/endsWith/ignoreCase flags break
        # the empty-string match-all, so keep the body minimal.
        body: dict[str, Any] = {
            "class": "SearchStringRequestBody",
            "searchString": search or "",
        }
        if search:
            body["ignoreCase"] = True
        try:
            r = self._http().post(
                f"{url}?startFrom=0&pageSize={page_size}",
                headers={
                    "Authorization": f"Bearer {tok}",
                    "Content-Type": "application/json",
                },
                content=_json.dumps(body),
            )
        except Exception:
            return []
        if r.status_code != 200:
            return []
        return self._elements(r)

    def _post(self, url: str, body: dict) -> Any:
        tok = self._bearer()
        return self._http().post(
            url,
            headers={
                "Authorization": f"Bearer {tok}",
                "Content-Type": "application/json",
            },
            content=_json.dumps(body),
        )

    # ── normalized list methods (consumed by the KG extractor) ───────────────
    def list_assets(self) -> list[dict]:
        # The asset-catalog in-domain search rejects an empty searchString (unlike
        # glossary-manager), so union a handful of broad substrings and dedupe by
        # GUID to approximate "all assets".
        seen: dict[str, dict] = {}
        # A few broad terms balance coverage vs. the view-server's per-query
        # latency (each by-search-string is a separate OMVS round-trip).
        for term in ("Server", "Data", "Coco"):
            for a in self._search(
                "asset-catalog", "assets/in-domain/by-search-string", search=term
            ):
                g = a.get("guid")
                if g and g not in seen:
                    seen[g] = a
        return list(seen.values())

    def list_glossary_terms(self) -> list[dict]:
        return self._search("glossary-manager", "glossaries/terms/by-search-string")

    def list_glossary_categories(self) -> list[dict]:
        return self._search(
            "glossary-manager", "glossaries/categories/by-search-string"
        )

    def list_governance_definitions(self) -> list[dict]:
        return self._search(
            "governance-officer", "governance-definitions/by-search-string"
        )

    def list_software_servers(self) -> list[dict]:
        # Software servers surface as assets of a server type in the catalog.
        return [
            a
            for a in self.list_assets()
            if "server" in str(a.get("typeName", "")).lower()
        ]

    def list_connections(self) -> list[dict]:
        return self._search(
            "asset-catalog", "assets/in-domain/by-search-string", search="Connection"
        )

    def list_data_flows(self) -> list[dict]:
        """Enumerate ``DataFlow`` lineage edges across the catalogue.

        CONCEPT:EA-KG.compute.bidirectional-kg-federation-powers — Bidirectional KG Federation. Powers KG federation: the
        ``egeria`` extractor turns these into ``flowsTo`` /
        ``dependsOn`` edges. Each record is ``{source, target, label, sourceName,
        targetName, sourceType, targetType}`` (GUIDs in source/target). Scans the
        low-cardinality hubs, so it captures every cross-layer edge without walking
        all assets.
        """
        try:
            from egeria_mcp.lineage_scan import catalog_lineage_edges

            return catalog_lineage_edges(self)
        except Exception:
            return []

    # ── comprehensive OMVS coverage (find by-search-string per service) ───────
    # Each method targets a confirmed (view-service marker, noun) pair. They share
    # the tolerant ``_search`` plumbing (empty ``search`` = match-all), so an
    # unseeded/locked catalog degrades to ``[]`` rather than raising.
    #
    # asset-catalog — assets, connections, infrastructure, technology
    def find_data_assets(self, search: str = "") -> list[dict]:
        return self._search("asset-catalog", "data-assets/by-search-string", search)

    def find_connections(self, search: str = "") -> list[dict]:
        return self._search("asset-catalog", "connections/by-search-string", search)

    def find_connector_types(self, search: str = "") -> list[dict]:
        return self._search("asset-catalog", "connector-types/by-search-string", search)

    def find_endpoints(self, search: str = "") -> list[dict]:
        return self._search("asset-catalog", "endpoints/by-search-string", search)

    def find_infrastructure_assets(self, search: str = "") -> list[dict]:
        return self._search(
            "asset-catalog", "infrastructure-assets/by-search-string", search
        )

    def find_technology_types(self, search: str = "") -> list[dict]:
        return self._search(
            "asset-catalog", "technology-types/by-search-string", search
        )

    # asset-maker / data-designer — schema + data design
    def find_schema_types(self, search: str = "") -> list[dict]:
        return self._search("asset-maker", "schema-types/by-search-string", search)

    def find_schema_attributes(self, search: str = "") -> list[dict]:
        return self._search("asset-maker", "schema-attributes/by-search-string", search)

    def find_data_structures(self, search: str = "") -> list[dict]:
        return self._search("data-designer", "data-structures/by-search-string", search)

    def find_data_fields(self, search: str = "") -> list[dict]:
        return self._search("data-designer", "data-fields/by-search-string", search)

    def find_data_value_specifications(self, search: str = "") -> list[dict]:
        return self._search(
            "data-designer", "data-value-specifications/by-search-string", search
        )

    # collection-manager — collections + digital products
    def find_collections(self, search: str = "Collection") -> list[dict]:
        # Empty match-all on collections is slow/times out — default to a term.
        return self._search(
            "collection-manager", "collections/by-search-string", search
        )

    def find_digital_products(self, search: str = "") -> list[dict]:
        return self._search(
            "collection-manager", "digital-products/by-search-string", search
        )

    # governance-officer — governance defs + external references
    def find_external_references(self, search: str = "") -> list[dict]:
        return self._search(
            "governance-officer", "external-references/by-search-string", search
        )

    # solution-architect — supply chains, blueprints, components
    def find_information_supply_chains(self, search: str = "") -> list[dict]:
        return self._search(
            "solution-architect", "information-supply-chains/by-search-string", search
        )

    def find_solution_blueprints(self, search: str = "") -> list[dict]:
        return self._search(
            "solution-architect", "solution-blueprints/by-search-string", search
        )

    def find_solution_components(self, search: str = "") -> list[dict]:
        return self._search(
            "solution-architect", "solution-components/by-search-string", search
        )

    # my-profile — actors, roles, identities
    def find_actor_profiles(self, search: str = "") -> list[dict]:
        return self._search("my-profile", "actor-profiles/by-search-string", search)

    def find_actor_roles(self, search: str = "") -> list[dict]:
        return self._search("my-profile", "actor-roles/by-search-string", search)

    def find_user_identities(self, search: str = "") -> list[dict]:
        return self._search("my-profile", "user-identities/by-search-string", search)

    # project-manager / community-matters / location-arena
    def find_projects(self, search: str = "") -> list[dict]:
        return self._search("project-manager", "projects/by-search-string", search)

    def find_communities(self, search: str = "") -> list[dict]:
        return self._search("community-matters", "communities/by-search-string", search)

    def find_locations(self, search: str = "") -> list[dict]:
        return self._search("location-arena", "locations/by-search-string", search)

    # reference-data — valid value definitions
    def find_valid_values(self, search: str = "") -> list[dict]:
        return self._search(
            "reference-data", "valid-value-definitions/by-search-string", search
        )

    # runtime-manager — registered metadata cohorts
    def find_cohorts(self, search: str = "") -> list[dict]:
        return self._search(
            "runtime-manager", "metadata-repository-cohorts/by-search-string", search
        )

    # generic full-coverage catch-all: any open-metadata element type
    def find_metadata_elements(self, search: str = "") -> list[dict]:
        """Search across all open-metadata element types (generic find)."""
        return self._search(
            "asset-catalog", "metadata-elements/by-search-string", search
        )

    def get_element(self, guid: str) -> dict:
        """Retrieve any element by GUID (with its classifications)."""
        return self._retrieve_element(guid)

    # ── granular query methods (back the MCP read tools) ─────────────────────
    def asset_search(self, query: str, type_filter: str = "") -> list[dict]:
        recs = self._search(
            "asset-catalog",
            "assets/in-domain/by-search-string",
            search=query or _SEARCH_ALL,
        )
        if type_filter:
            tf = type_filter.lower()
            recs = [r for r in recs if tf in str(r.get("typeName", "")).lower()]
        return recs

    def glossary_lookup(self, term: str, glossary: str = "") -> list[dict]:
        return self._search(
            "glossary-manager",
            "glossaries/terms/by-search-string",
            search=term or _SEARCH_ALL,
        )

    def glossary_categories(self) -> list[dict]:
        return self.list_glossary_categories()

    def lineage(self, asset_guid: str, direction: str = "both", depth: int = 2) -> dict:
        """Return the asset lineage graph (``AssetLineageGraph``) for a GUID.

        Unwraps the response envelope to the inner graph element, which carries
        the connected edges in ``lineageLinkage`` (and ``lineageRelationships``).
        """
        try:
            url = self._omvs("asset-catalog", f"assets/{asset_guid}/as-lineage-graph")
            # Egeria's AssetLineageGraphRequestBody rejects unknown fields; send the
            # minimal valid body (it defaults effective time / traversal itself).
            r = self._post(url, {"class": "AssetLineageGraphRequestBody"})
            if r.status_code == 200:
                el = (r.json() or {}).get("element") or {}
                el.setdefault("guid", asset_guid)
                return el
            return {"guid": asset_guid, "httpCode": r.status_code, "lineageLinkage": []}
        except Exception:
            return {"error": "Operation failed", "guid": asset_guid}

    def _retrieve_element(self, guid: str) -> dict:
        """Retrieve a full asset element (incl. its classifications).

        ``asset-maker``'s retrieve is the endpoint that surfaces applied
        classifications; Egeria attaches each as a *named* ``elementHeader``
        entry (``elementHeader.confidentiality`` …), an ``ElementClassification``
        — not a ``classifications`` list.
        """
        try:
            r = self._post(
                self._omvs("asset-maker", f"assets/{guid}/retrieve"),
                {"class": "AnyTimeRequestBody"},
            )
        except Exception:
            return {"error": "Operation failed"}
        if r.status_code != 200:
            return {"httpCode": r.status_code}
        try:
            return (r.json() or {}).get("element") or {}
        except Exception:
            return {}

    def governance_for(self, element_guid: str) -> dict:
        """Return classifications + confidentiality level applying to an element.

        Flattens the named ``elementHeader`` classification entries into a simple
        ``[{name, level?}]`` list and surfaces the integer ``confidentialityLevel``
        (Egeria scale: 0 Unclassified, 1 Internal, 2 Confidential, 3 Sensitive,
        4 Restricted) that :func:`governed_route` thresholds on.
        """
        el = self._retrieve_element(element_guid)
        if not isinstance(el, dict) or "elementHeader" not in el:
            return {
                "guid": element_guid,
                "classifications": [],
                "confidentialityLevel": None,
                "httpCode": el.get("httpCode") if isinstance(el, dict) else None,
            }
        header = el.get("elementHeader") or {}
        classifications: list[dict] = []
        conf_level: int | None = None
        for key, val in header.items():
            if not isinstance(val, dict) or val.get("class") != "ElementClassification":
                continue
            name = val.get("classificationName") or key
            if name.lower() in ("anchors", "anchor"):
                continue  # structural anchor, not a governance classification
            props = val.get("classificationProperties") or {}
            entry: dict[str, Any] = {"name": name}
            if "confidentialityLevel" in props:
                entry["level"] = props["confidentialityLevel"]
                if name.lower().startswith("confidential"):
                    conf_level = props["confidentialityLevel"]
            classifications.append(entry)
        return {
            "guid": element_guid,
            "classifications": classifications,
            "confidentialityLevel": conf_level,
            "httpCode": 200,
        }

    def list_policies(self, domain: str = "") -> list[dict]:
        recs = [
            r
            for r in self.list_governance_definitions()
            if "principle" not in str(r.get("typeName", "")).lower()
        ]
        if domain:
            dl = domain.lower()
            recs = [r for r in recs if dl in str(r.get("domain", "")).lower()]
        return recs

    # ── idempotency finders (match by qualifiedName) ─────────────────────────
    def find_glossary(self, qualified_name: str) -> str | None:
        """Return the GUID of an existing glossary by qualifiedName, or None."""
        for el in self._search(
            "collection-manager", "collections/by-search-string", search=qualified_name
        ):
            if el.get("qualifiedName") == qualified_name:
                return el.get("guid")
        return None

    def find_term(self, qualified_name: str) -> str | None:
        """Return the GUID of an existing glossary term by qualifiedName, or None."""
        for el in self._search(
            "glossary-manager",
            "glossaries/terms/by-search-string",
            search=qualified_name,
        ):
            if el.get("qualifiedName") == qualified_name:
                return el.get("guid")
        return None

    def find_asset(self, qualified_name: str) -> str | None:
        """Return the GUID of an existing asset by qualifiedName, or None."""
        for el in self._search(
            "asset-catalog", "assets/in-domain/by-search-string", search=qualified_name
        ):
            if el.get("qualifiedName") == qualified_name:
                return el.get("guid")
        return None

    # ── write methods (gated by enable_write) ────────────────────────────────
    def _require_write(self) -> None:
        if not self.enable_write:
            raise EgeriaWriteDisabled(
                "Egeria writes are disabled — set EGERIA_ENABLE_WRITE=true to enable."
            )

    def _create(self, service: str, sub_path: str, body: dict) -> dict:
        """POST a create request; return ``{guid?, httpCode, error?}``."""
        self._require_write()
        try:
            r = self._post(self._omvs(service, sub_path), body)
        except Exception:
            return {"error": "Operation failed"}
        out: dict[str, Any] = {"httpCode": r.status_code}
        try:
            j = r.json() or {}
            if j.get("guid"):
                out["guid"] = j["guid"]
            if j.get("exceptionErrorMessage"):
                out["error"] = j["exceptionErrorMessage"]
        except Exception:
            out["body"] = r.text[:300]
        return out

    def create_glossary(
        self,
        display_name: str,
        description: str = "",
        *,
        usage: str = "",
        language: str = "English",
    ) -> dict:
        """Create (or reuse) a business glossary; returns ``{guid, reused?}``."""
        qn = f"Glossary::{_slug(display_name)}"
        existing = self.find_glossary(qn)
        if existing:
            return {"guid": existing, "httpCode": 200, "reused": True}
        res = self._create(
            "collection-manager",
            "collections",
            {
                "class": "NewElementRequestBody",
                "isOwnAnchor": True,
                "properties": {
                    "class": "GlossaryProperties",
                    "displayName": display_name,
                    "qualifiedName": qn,
                    "description": description,
                    "usage": usage,
                    "language": language,
                },
            },
        )
        res["qualifiedName"] = qn
        return res

    def create_term(
        self, glossary: str, name: str, definition: str = "", *, description: str = ""
    ) -> dict:
        """Create (or reuse) a glossary term anchored to ``glossary`` (its GUID).

        ``definition`` populates the term ``summary``; ``description`` the longer
        prose. Returns ``{guid, reused?}``.
        """
        qn = f"Term::{_slug(name)}"
        existing = self.find_term(qn)
        if existing:
            return {"guid": existing, "httpCode": 200, "reused": True}
        res = self._create(
            "glossary-manager",
            "glossaries/terms",
            {
                "class": "NewElementRequestBody",
                "parentGUID": glossary,
                "parentRelationshipTypeName": "CollectionMembership",
                "isOwnAnchor": True,
                "parentAtEnd1": True,
                "properties": {
                    "class": "GlossaryTermProperties",
                    "qualifiedName": qn,
                    "displayName": name,
                    "summary": definition,
                    "description": description,
                },
            },
        )
        res["qualifiedName"] = qn
        return res

    def create_asset(
        self,
        type_name: str,
        qualified_name: str,
        display_name: str,
        *,
        description: str = "",
        deployed_implementation_type: str = "",
        confidentiality_level: int | None = None,
        additional_properties: dict | None = None,
    ) -> dict:
        """Create (or reuse) a data asset, optionally classified at creation.

        ``type_name`` is an Egeria open-metadata asset type (e.g.
        ``SoftwareServer``, ``RelationalDatabase``, ``DeployedDatabaseSchema``,
        ``KafkaTopic``). When ``confidentiality_level`` is given the asset is born
        with a ``Confidentiality`` classification at that level. Returns
        ``{guid, reused?}``.
        """
        existing = self.find_asset(qualified_name)
        if existing:
            if confidentiality_level is not None:
                self.set_confidentiality(existing, confidentiality_level)
            return {"guid": existing, "httpCode": 200, "reused": True}
        props: dict[str, Any] = {
            "class": "AssetProperties",
            "typeName": type_name,
            "qualifiedName": qualified_name,
            "displayName": display_name,
            "description": description,
        }
        if deployed_implementation_type:
            props["deployedImplementationType"] = deployed_implementation_type
        if additional_properties:
            # Free-form map on Referenceable — accepted for any type (unlike
            # extendedProperties, which Egeria validates against the type def).
            props["additionalProperties"] = {
                k: str(v) for k, v in additional_properties.items()
            }
        body: dict[str, Any] = {
            "class": "NewElementRequestBody",
            "isOwnAnchor": True,
            "properties": props,
        }
        if confidentiality_level is not None:
            body["initialClassifications"] = {
                "Confidentiality": {
                    "class": "ConfidentialityProperties",
                    "confidentialityLevel": confidentiality_level,
                    "confidence": 100,
                    "statusIdentifier": 1,
                }
            }
        res = self._create("asset-maker", "assets", body)
        res["qualifiedName"] = qualified_name
        return res

    def set_confidentiality(self, element_guid: str, level: int) -> dict:
        """Apply/refresh a ``Confidentiality`` classification at ``level`` (0–4)."""
        res = self._create(
            "classification-explorer",
            f"elements/{element_guid}/confidentiality",
            {
                "class": "NewClassificationRequestBody",
                "properties": {
                    "class": "ConfidentialityProperties",
                    "confidentialityLevel": level,
                    "confidence": 100,
                    "statusIdentifier": 1,
                },
            },
        )
        res["level"] = level
        return res

    # Back-compat alias for the generic MCP classify tool.
    def classify(self, element_guid: str, classification: str, properties: dict) -> Any:
        if classification.lower().startswith("confidential"):
            level = int((properties or {}).get("confidentialityLevel", 0))
            return self.set_confidentiality(element_guid, level)
        return self._create(
            "classification-explorer",
            f"elements/{element_guid}/{classification.lower()}",
            {"class": "NewClassificationRequestBody", "properties": properties or {}},
        )

    def link_data_flow(
        self,
        source_guid: str,
        target_guid: str,
        *,
        label: str = "",
        description: str = "",
    ) -> dict:
        """Create a ``DataFlow`` lineage edge ``source → target``."""
        sub = (
            f"from-elements/{source_guid}/via/DataFlow/to-elements/{target_guid}/attach"
        )
        props: dict[str, Any] = {"class": "DataFlowProperties"}
        if label:
            props["label"] = label
        if description:
            props["description"] = description
        return self._create(
            "lineage-linker",
            sub,
            {"class": "NewRelationshipRequestBody", "properties": props},
        )

    def assert_lineage(
        self, source_guid: str, process_guid: str, target_guid: str
    ) -> Any:
        """Assert source → process → target as two ``DataFlow`` edges."""
        return {
            "edges": [
                self.link_data_flow(source_guid, process_guid, label="produces"),
                self.link_data_flow(process_guid, target_guid, label="produces"),
            ]
        }

    def create_collection(
        self, display_name: str, description: str = "", *, category: str = ""
    ) -> dict:
        """Create (or reuse) a collection (e.g. a digital-product folder)."""
        qn = f"Collection::{_slug(display_name)}"
        existing = self.find_glossary(qn)  # collections share the find endpoint
        if existing:
            return {"guid": existing, "httpCode": 200, "reused": True}
        props: dict[str, Any] = {
            "class": "CollectionProperties",
            "displayName": display_name,
            "qualifiedName": qn,
            "description": description,
        }
        if category:
            props["collectionType"] = category
        res = self._create(
            "collection-manager",
            "collections",
            {
                "class": "NewElementRequestBody",
                "isOwnAnchor": True,
                "properties": props,
            },
        )
        res["qualifiedName"] = qn
        return res

    def create_project(self, display_name: str, description: str = "") -> dict:
        """Create (or reuse) a project."""
        qn = f"Project::{_slug(display_name)}"
        res = self._create(
            "project-manager",
            "projects",
            {
                "class": "NewElementRequestBody",
                "isOwnAnchor": True,
                "properties": {
                    "class": "ProjectProperties",
                    "name": display_name,
                    "qualifiedName": qn,
                    "description": description,
                },
            },
        )
        res["qualifiedName"] = qn
        return res

    def set_classification(
        self, element_guid: str, classification: str, properties: dict | None = None
    ) -> dict:
        """Apply any classification to an element (generic).

        ``Confidentiality`` is routed through :meth:`set_confidentiality` so the
        ``confidentialityLevel`` bean field is set correctly.
        """
        return self.classify(element_guid, classification, properties or {})

    def delete_element(self, element_guid: str) -> dict:
        """Delete an asset element by GUID."""
        return self._create(
            "asset-maker",
            f"assets/{element_guid}/delete",
            {"class": "DeleteElementRequestBody"},
        )
