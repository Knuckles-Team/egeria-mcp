"""Network harvest — the Technitium DNS layer.

Reads authoritative zones live from a Technitium DNS server and catalogs each as an
Egeria ``Collection`` (a DNS zone groups records) — the network namespace joins the
catalog. Idempotent.

Config-driven (``TECHNITIUM_DNS_URL`` + ``TECHNITIUM_DNS_TOKEN``); tolerant.
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


def fetch_zones(
    url: str, token: str, *, tls_profile: ResolvedTLSProfile | None = None
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(timeout=20.0, **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs()) as c:
            r = c.get(f"{url.rstrip('/')}/api/zones/list", params={"token": token})
        if r.status_code != 200:
            return []
        return ((r.json() or {}).get("response") or {}).get("zones") or []
    except Exception:
        return []


def harvest_dns(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog Technitium DNS zones into Egeria as Collections."""
    report: dict[str, Any] = {"zones": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or setting("TECHNITIUM_DNS_URL")
    token = token or setting("TECHNITIUM_DNS_TOKEN")
    if not url or not token:
        report["skipped"] = (
            "no Technitium creds (set TECHNITIUM_DNS_URL / TECHNITIUM_DNS_TOKEN)"
        )
        return report

    zones = fetch_zones(url, token, tls_profile=tls_profile)
    report["source"] = {"url": url, "zones": len(zones)}
    if not zones:
        report["skipped"] = "no zones returned (unreachable or unauthorized)"
        return report

    for z in zones:
        name = z.get("name")
        if not name:
            continue
        res = api.create_collection(
            f"DNS Zone {name}",
            description=f"DNS zone '{name}' ({z.get('type')}).",
            category="DNSZone",
        )
        record_error(f"zone:{name}", res)
        report["zones"].append({"name": name, "type": z.get("type"), **res})

    report["summary"] = {
        "zones": len([z for z in report["zones"] if z.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
