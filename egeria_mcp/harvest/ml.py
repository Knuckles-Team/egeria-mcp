"""ML harvest — the data-science layer.

Reads models and training datasets live from the data-science service and catalogs
models as Egeria ``DeployedSoftwareComponent`` assets and datasets as
``DeployedDatabaseSchema`` — model + training-data governance/lineage. Idempotent.

Config-driven (``DATA_SCIENCE_MCP_URL`` + ``DATA_SCIENCE_MCP_TOKEN``); tolerant.
"""

from __future__ import annotations

import os
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def _fetch(url: str, token: str | None, path: str, verify_ssl: bool) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(f"{url.rstrip('/')}{path}", headers=headers)
        if r.status_code != 200:
            return []
        data = r.json()
        recs = data.get("data") if isinstance(data, dict) else data
        return recs if isinstance(recs, list) else []
    except Exception:
        return []


def harvest_ml(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog ML models + datasets into Egeria."""
    report: dict[str, Any] = {"models": [], "datasets": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or os.getenv("DATA_SCIENCE_MCP_URL") or os.getenv("DATA_SCIENCE_URL")
    token = (
        token or os.getenv("DATA_SCIENCE_MCP_TOKEN") or os.getenv("DATA_SCIENCE_TOKEN")
    )
    if not url:
        report["skipped"] = "no data-science URL (set DATA_SCIENCE_MCP_URL)"
        return report

    models = _fetch(url, token, "/api/models", verify_ssl)
    datasets = _fetch(url, token, "/api/datasets", verify_ssl)
    report["source"] = {"url": url, "models": len(models), "datasets": len(datasets)}
    if not models and not datasets:
        report["skipped"] = "no models/datasets returned (unreachable or unauthorized)"
        return report

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
        record_error(f"model:{name}", res)
        report["models"].append({"name": str(name), **res})
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
        record_error(f"dataset:{name}", res)
        report["datasets"].append({"name": str(name), **res})

    report["summary"] = {
        "models": len([m for m in report["models"] if m.get("guid")]),
        "datasets": len([d for d in report["datasets"] if d.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
