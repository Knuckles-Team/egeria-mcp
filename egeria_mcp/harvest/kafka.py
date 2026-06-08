"""Streaming harvest — the Kafka layer.

Reads topics live from a Kafka REST Proxy and catalogs each as an Egeria data asset
(Kafka topics are the event-lineage backbone of the estate). Idempotent.

Config-driven (``KAFKA_REST_URL``, optional ``KAFKA_TOKEN``); tolerant. (A REST proxy
is required because Kafka's native topic admin is not HTTP.)
"""

from __future__ import annotations

import os
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False

_INTERNAL_PREFIXES = ("__", "_confluent", "_schemas")


def fetch_topics(
    rest_url: str, token: str | None, *, verify_ssl: bool = False
) -> list[str]:
    """Fetch topic names from a Confluent-style Kafka REST Proxy (v2 or v3)."""
    if not HTTPX_AVAILABLE:
        return []
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
            r = c.get(f"{rest_url.rstrip('/')}/topics", headers=headers)
        if r.status_code != 200:
            return []
        data = r.json()
        if isinstance(data, list):  # v2: ["t1", "t2"]
            return [t for t in data if isinstance(t, str)]
        if isinstance(data, dict):  # v3: {"data": [{"topic_name": ...}]}
            return [
                d.get("topic_name") for d in data.get("data", []) if d.get("topic_name")
            ]
    except Exception:
        return []
    return []


def harvest_kafka(
    api: Any,
    rest_url: str | None = None,
    token: str | None = None,
    *,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog Kafka topics into Egeria as data assets."""
    report: dict[str, Any] = {"topics": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    rest_url = rest_url or os.getenv("KAFKA_REST_URL")
    token = token or os.getenv("KAFKA_TOKEN")
    if not rest_url:
        report["skipped"] = "no Kafka REST proxy (set KAFKA_REST_URL)"
        return report

    topics = [
        t
        for t in fetch_topics(rest_url, token, verify_ssl=verify_ssl)
        if not t.startswith(_INTERNAL_PREFIXES)
    ]
    report["source"] = {"rest_url": rest_url, "topics": len(topics)}
    if not topics:
        report["skipped"] = "no topics returned (unreachable or empty)"
        return report

    for topic in topics:
        qn = f"Topic::Kafka::{topic}"
        res = api.create_asset(
            "DeployedDatabaseSchema",
            qn,
            topic,
            description=f"Kafka topic '{topic}'.",
            deployed_implementation_type="Kafka Topic",
            confidentiality_level=1,
            additional_properties={"topic": topic, "source": "Kafka"},
        )
        record_error(f"topic:{topic}", res)
        report["topics"].append({"topic": topic, "qualifiedName": qn, **res})

    report["summary"] = {
        "topics": len([t for t in report["topics"] if t.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
