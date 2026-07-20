"""Semantic-store harvest — the Apache Jena (Fuseki) layer.

Reads Fuseki datasets live and catalogs each as an Egeria data asset — the RDF
triplestore joins the same system-of-record as the KG. Idempotent.

Config-driven (``JENA_FUSEKI_URL`` / ``JENA_URL`` + optional ``JENA_USERNAME`` /
``JENA_PASSWORD`` or ``JENA_TOKEN``); tolerant.
"""

from __future__ import annotations

from typing import Any

from agent_utilities.core.config import setting
from agent_utilities.core.transport_security import (
    ResolvedTLSProfile,
    resolve_tls_profile,
)

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def fetch_datasets(
    url: str,
    *,
    auth=None,
    token: str | None = None,
    tls_profile: ResolvedTLSProfile | None = None,
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        with httpx.Client(timeout=20.0, **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs()) as c:
            r = c.get(f"{url.rstrip('/')}/$/datasets", auth=auth, headers=headers)
        if r.status_code != 200:
            return []
        return (r.json() or {}).get("datasets") or []
    except Exception:
        return []


def harvest_semantic(
    api: Any, url: str | None = None, *, tls_profile: ResolvedTLSProfile | None = None
) -> dict[str, Any]:
    """Catalog Apache Jena Fuseki datasets into Egeria as data assets."""
    report: dict[str, Any] = {"datasets": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or setting("JENA_FUSEKI_URL") or setting("JENA_URL")
    user, password = setting("JENA_USERNAME"), setting("JENA_PASSWORD")
    token = setting("JENA_TOKEN")
    if not url:
        report["skipped"] = "no Jena Fuseki URL (set JENA_FUSEKI_URL)"
        return report

    datasets = fetch_datasets(
        url,
        auth=(user, password) if user and password else None,
        token=token,
        tls_profile=tls_profile,
    )
    report["source"] = {"url": url, "datasets": len(datasets)}
    if not datasets:
        report["skipped"] = "no datasets returned (unreachable or unauthorized)"
        return report

    store = api.create_asset(
        "SoftwareServer",
        "DataStore::fuseki",
        "jena-fuseki",
        description="Apache Jena Fuseki RDF triplestore.",
        deployed_implementation_type="Apache Jena Fuseki",
        confidentiality_level=1,
    )
    record_error("store:fuseki", store)
    store_guid = store.get("guid")

    for ds in datasets:
        name = (ds.get("ds.name") or ds.get("name") or "").lstrip("/")
        if not name:
            continue
        qn = f"Dataset::Jena::{name}"
        res = api.create_asset(
            "DeployedDatabaseSchema",
            qn,
            name,
            description=f"Jena Fuseki RDF dataset '{name}'.",
            deployed_implementation_type="RDF Dataset",
            confidentiality_level=1,
            additional_properties={"dataset": name, "source": "Jena"},
        )
        record_error(f"dataset:{name}", res)
        report["datasets"].append({"name": name, **res})
        if store_guid and res.get("guid"):
            api.link_data_flow(store_guid, res["guid"], label="hosts")

    report["summary"] = {
        "datasets": len([d for d in report["datasets"] if d.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
