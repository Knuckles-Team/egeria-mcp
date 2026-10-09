"""ML harvest — the data-science layer.

Reads models and training datasets live from the data-science service and catalogs
models as Egeria ``DeployedSoftwareComponent`` assets and datasets as
``DeployedDatabaseSchema`` — model + training-data governance/lineage. Idempotent.

Config-driven (``DATA_SCIENCE_MCP_URL`` + ``DATA_SCIENCE_MCP_TOKEN``); tolerant.
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


def _fetch(
    url: str, token: str | None, path: str, tls_profile: ResolvedTLSProfile | None
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        with httpx.Client(
            timeout=20.0,
            **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs(),
        ) as c:
            r = c.get(f"{url.rstrip('/')}{path}", headers=headers)
        if r.status_code != 200:
            return []
        data = r.json()
        recs = data.get("data") if isinstance(data, dict) else data
        return recs if isinstance(recs, list) else []
    except Exception:
        return []


def _catalog_models(api: Any, models: list[dict], report: dict[str, Any]) -> None:
    """Catalog ML models as ``DeployedSoftwareComponent`` assets."""
    for m in models:
        name = m.get("name") or m.get("id")
        if not name:
            continue
        res = api.create_asset(
            "DeployedSoftwareComponent",
            f"Model::{name}",
            str(name),
            description=f"ML model '{name}'.",
            deployed_implementation_type=m.get("framework") or "ML Model",
            confidentiality_level=1,
            additional_properties={
                "framework": m.get("framework"),
                "source": "DataScience",
            },
        )
        note_error(report, f"model:{name}", res)
        report["models"].append({"name": str(name), **res})


def _catalog_datasets(api: Any, datasets: list[dict], report: dict[str, Any]) -> None:
    """Catalog ML training datasets as ``DeployedDatabaseSchema`` assets."""
    for d in datasets:
        name = d.get("name") or d.get("id")
        if not name:
            continue
        res = api.create_asset(
            "DeployedDatabaseSchema",
            f"Dataset::ML::{name}",
            str(name),
            description=f"ML training dataset '{name}'.",
            deployed_implementation_type="Training Dataset",
            confidentiality_level=2,
            additional_properties={"source": "DataScience"},
        )
        note_error(report, f"dataset:{name}", res)
        report["datasets"].append({"name": str(name), **res})


def harvest_ml(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog ML models + datasets into Egeria."""
    report: dict[str, Any] = {"models": [], "datasets": [], "errors": []}

    url = url or setting("DATA_SCIENCE_MCP_URL") or setting("DATA_SCIENCE_URL")
    token = token or setting("DATA_SCIENCE_MCP_TOKEN") or setting("DATA_SCIENCE_TOKEN")
    if not url:
        report["skipped"] = "no data-science URL (set DATA_SCIENCE_MCP_URL)"
        return report

    models = _fetch(url, token, "/api/models", tls_profile)
    datasets = _fetch(url, token, "/api/datasets", tls_profile)
    report["source"] = {"url": url, "models": len(models), "datasets": len(datasets)}
    if not models and not datasets:
        report["skipped"] = "no models/datasets returned (unreachable or unauthorized)"
        return report

    _catalog_models(api, models, report)
    _catalog_datasets(api, datasets, report)

    report["summary"] = {
        "models": count_created(report["models"]),
        "datasets": count_created(report["datasets"]),
        "errors": len(report["errors"]),
    }
    return report
