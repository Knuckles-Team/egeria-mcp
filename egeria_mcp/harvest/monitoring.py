"""Monitoring harvest — the Uptime Kuma layer.

Reads monitors from Uptime Kuma's Prometheus ``/metrics`` endpoint and catalogs each
monitored target as an Egeria ``DeployedSoftwareComponent`` — the monitored-service
inventory joins the catalog and reconciles with the container/ingress layers.
Idempotent.

Config-driven (``UPTIME_KUMA_URL`` + ``UPTIME_KUMA_TOKEN`` = metrics API key);
tolerant.
"""

from __future__ import annotations

import re
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

_NAME = re.compile(r'monitor_name="([^"]+)"')
_TYPE = re.compile(r'monitor_type="([^"]+)"')


def _parse_monitor_names(metrics_text: str) -> list[dict]:
    """Distinct {name, type} monitors from Uptime Kuma's Prometheus text."""
    seen: dict[str, str] = {}
    for line in metrics_text.splitlines():
        if not (
            line.startswith("monitor_status") or line.startswith("monitor_response_time")
        ):
            continue
        n = _NAME.search(line)
        if n and n.group(1) not in seen:
            t = _TYPE.search(line)
            seen[n.group(1)] = t.group(1) if t else ""
    return [{"name": k, "type": v} for k, v in seen.items()]


def fetch_monitors(
    url: str, token: str, *, tls_profile: ResolvedTLSProfile | None = None
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(
            timeout=20.0,
            **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs(),
        ) as c:
            r = c.get(f"{url.rstrip('/')}/metrics", auth=("", token))
        if r.status_code != 200:
            return []
    except Exception:
        return []
    return _parse_monitor_names(r.text)


def harvest_monitoring(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog Uptime Kuma monitors into Egeria as monitored-service assets."""
    report: dict[str, Any] = {"monitors": [], "errors": []}

    url = url or setting("UPTIME_KUMA_URL")
    token = token or setting("UPTIME_KUMA_TOKEN")
    if not url or not token:
        report["skipped"] = (
            "no Uptime Kuma URL/token (set UPTIME_KUMA_URL / UPTIME_KUMA_TOKEN)"
        )
        return report

    monitors = fetch_monitors(url, token, tls_profile=tls_profile)
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
        note_error(report, f"monitor:{name}", res)
        report["monitors"].append({"name": name, **res})

    report["summary"] = {
        "monitors": count_created(report["monitors"]),
        "errors": len(report["errors"]),
    }
    return report
