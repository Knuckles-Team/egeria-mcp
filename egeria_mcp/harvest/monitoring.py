"""Monitoring harvest — the Uptime Kuma layer.

Reads monitors from Uptime Kuma's Prometheus ``/metrics`` endpoint and catalogs each
monitored target as an Egeria ``DeployedSoftwareComponent`` — the monitored-service
inventory joins the catalog and reconciles with the container/ingress layers.
Idempotent.

Config-driven (``UPTIME_KUMA_URL`` + ``UPTIME_KUMA_TOKEN`` = metrics API key);
tolerant.
"""

from __future__ import annotations

import os
import re
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False

_NAME = re.compile(r'monitor_name="([^"]+)"')
_TYPE = re.compile(r'monitor_type="([^"]+)"')


def fetch_monitors(url: str, token: str, *, verify_ssl: bool = False) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(f"{url.rstrip('/')}/metrics", auth=("", token))
        if r.status_code != 200:
            return []
    except Exception:
        return []
    seen: dict[str, str] = {}
    for line in r.text.splitlines():
        if line.startswith("monitor_status") or line.startswith(
            "monitor_response_time"
        ):
            n = _NAME.search(line)
            if n and n.group(1) not in seen:
                t = _TYPE.search(line)
                seen[n.group(1)] = t.group(1) if t else ""
    return [{"name": k, "type": v} for k, v in seen.items()]


def harvest_monitoring(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog Uptime Kuma monitors into Egeria as monitored-service assets."""
    report: dict[str, Any] = {"monitors": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or os.getenv("UPTIME_KUMA_URL")
    token = token or os.getenv("UPTIME_KUMA_TOKEN")
    if not url or not token:
        report["skipped"] = (
            "no Uptime Kuma URL/token (set UPTIME_KUMA_URL / UPTIME_KUMA_TOKEN)"
        )
        return report

    monitors = fetch_monitors(url, token, verify_ssl=verify_ssl)
    report["source"] = {"url": url, "monitors": len(monitors)}
    if not monitors:
        report["skipped"] = "no monitors returned (unreachable or unauthorized)"
        return report

    for m in monitors:
        name = m["name"]
        res = api.create_asset(
            "DeployedSoftwareComponent",
            f"Monitor::{name}",
            name,
            description=f"Uptime Kuma monitor '{name}' ({m.get('type') or '?'}).",
            deployed_implementation_type=f"Monitor ({m.get('type') or 'service'})",
            confidentiality_level=1,
            additional_properties={
                "monitorType": m.get("type"),
                "source": "UptimeKuma",
            },
        )
        record_error(f"monitor:{name}", res)
        report["monitors"].append({"name": name, **res})

    report["summary"] = {
        "monitors": len([m for m in report["monitors"] if m.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
