"""Vector-store harvest — the Qdrant/vector layer.

Reads collections live from a Qdrant vector database and catalogs each as an Egeria
data asset under the vector store — embedding collections join the catalog.
Idempotent.

Config-driven (``QDRANT_URL`` + optional ``QDRANT_API_KEY``); tolerant.
"""

from __future__ import annotations

from typing import Any

from agent_connector_sdk.config import setting
from agent_connector_sdk.tls.profile import ResolvedTLSProfile
from agent_connector_sdk.tls.resolve import resolve_tls_profile

from egeria_mcp.harvest._reporting import count_created, note_error

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def _collection_names(payload: dict) -> list[str]:
    cols = (((payload or {}).get("result") or {}).get("collections")) or []
    return [c.get("name") for c in cols if c.get("name")]


def fetch_collections(
    url: str, api_key: str | None, *, tls_profile: ResolvedTLSProfile | None = None
) -> list[str]:
    if not HTTPX_AVAILABLE:
        return []
    headers = {"api-key": api_key} if api_key else {}
    try:
        with httpx.Client(
            timeout=20.0,
            **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs(),
        ) as c:
            r = c.get(f"{url.rstrip('/')}/collections", headers=headers)
        return _collection_names(r.json()) if r.status_code == 200 else []
    except Exception:
        return []


def harvest_vectors(
    api: Any,
    url: str | None = None,
    api_key: str | None = None,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog Qdrant vector collections into Egeria as data assets."""
    report: dict[str, Any] = {"collections": [], "errors": []}

    url = url or setting("QDRANT_URL") or setting("VECTOR_URL")
    api_key = api_key or setting("QDRANT_API_KEY") or setting("VECTOR_TOKEN")
    if not url:
        report["skipped"] = "no vector store URL (set QDRANT_URL)"
        return report

    cols = fetch_collections(url, api_key, tls_profile=tls_profile)
    report["source"] = {"url": url, "collections": len(cols)}
    if not cols:
        report["skipped"] = "no collections returned (unreachable or empty)"
        return report

    store = api.create_asset(
        "SoftwareServer",
        "DataStore::qdrant",
        "qdrant",
        description="Qdrant vector store.",
        deployed_implementation_type="Qdrant",
        confidentiality_level=1,
    )
    note_error(report, "store:qdrant", store)
    store_guid = store.get("guid")

    for name in cols:
        qn = f"Dataset::Qdrant::{name}"
        res = api.create_asset(
            "DeployedDatabaseSchema",
            qn,
            name,
            description=f"Qdrant vector collection '{name}'.",
            deployed_implementation_type="Vector Collection",
            confidentiality_level=1,
            additional_properties={"collection": name, "source": "Qdrant"},
        )
        note_error(report, f"collection:{name}", res)
        report["collections"].append({"name": name, **res})
        if store_guid and res.get("guid"):
            api.link_data_flow(store_guid, res["guid"], label="hosts")

    report["summary"] = {
        "collections": count_created(report["collections"]),
        "errors": len(report["errors"]),
    }
    return report
