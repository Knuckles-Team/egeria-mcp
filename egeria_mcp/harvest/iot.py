"""IoT harvest — the Home Assistant layer.

Reads entity states live from Home Assistant and catalogs the instance as a
``SoftwareServer`` plus each integration **domain** (light, switch, sensor, …) as an
Egeria ``Collection`` — the smart-home estate joins the catalog without exploding
into thousands of individual entities. Idempotent.

Config-driven (``HOME_ASSISTANT_URL`` + ``HOME_ASSISTANT_TOKEN`` bearer); tolerant.
"""

from __future__ import annotations

import os
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def fetch_states(url: str, token: str, *, verify_ssl: bool = False) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(
                f"{url.rstrip('/')}/api/states",
                headers={"Authorization": f"Bearer {token}"},
            )
        if r.status_code != 200:
            return []
        data = r.json()
        return data if isinstance(data, list) else []
    except Exception:
        return []


def harvest_iot(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog Home Assistant integration domains into Egeria as Collections."""
    report: dict[str, Any] = {"domains": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or os.getenv("HOME_ASSISTANT_URL")
    token = token or os.getenv("HOME_ASSISTANT_TOKEN")
    if not url or not token:
        report["skipped"] = (
            "no Home Assistant URL/token (set HOME_ASSISTANT_URL / HOME_ASSISTANT_TOKEN)"
        )
        return report

    states = fetch_states(url, token, verify_ssl=verify_ssl)
    report["source"] = {"url": url, "entities": len(states)}
    if not states:
        report["skipped"] = "no entities returned (unreachable or unauthorized)"
        return report

    store = api.create_asset(
        "SoftwareServer",
        "DataStore::homeassistant",
        "home-assistant",
        description="Home Assistant smart-home hub.",
        deployed_implementation_type="Home Assistant",
        confidentiality_level=1,
    )
    record_error("store:homeassistant", store)

    domains: dict[str, int] = {}
    for st in states:
        eid = st.get("entity_id", "")
        if "." in eid:
            domains[eid.split(".", 1)[0]] = domains.get(eid.split(".", 1)[0], 0) + 1
    for domain, count in sorted(domains.items()):
        res = api.create_collection(
            f"HA {domain}",
            description=f"Home Assistant '{domain}' domain ({count} entities).",
            category="HomeAssistantDomain",
        )
        record_error(f"domain:{domain}", res)
        report["domains"].append({"domain": domain, "entities": count, **res})

    report["summary"] = {
        "domains": len([d for d in report["domains"] if d.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
