"""IoT harvest — the Home Assistant layer.

Reads entity states live from Home Assistant and catalogs the instance as a
``SoftwareServer`` plus each integration **domain** (light, switch, sensor, …) as an
Egeria ``Collection`` — the smart-home estate joins the catalog without exploding
into thousands of individual entities. Idempotent.

Config-driven (``HOME_ASSISTANT_URL`` + ``HOME_ASSISTANT_TOKEN`` bearer); tolerant.
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


def fetch_states(
    url: str, token: str, *, tls_profile: ResolvedTLSProfile | None = None
) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    try:
        with httpx.Client(timeout=20.0, **(tls_profile or resolve_tls_profile("EGERIA")).httpx_kwargs()) as c:
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
    tls_profile: ResolvedTLSProfile | None = None,
) -> dict[str, Any]:
    """Catalog Home Assistant integration domains into Egeria as Collections."""
    report: dict[str, Any] = {"domains": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or setting("HOME_ASSISTANT_URL")
    token = token or setting("HOME_ASSISTANT_TOKEN")
    if not url or not token:
        report["skipped"] = (
            "no Home Assistant URL/token (set HOME_ASSISTANT_URL / HOME_ASSISTANT_TOKEN)"
        )
        return report

    states = fetch_states(url, token, tls_profile=tls_profile)
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
