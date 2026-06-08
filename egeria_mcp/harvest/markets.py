"""Markets/finance harvest — the emerald-exchange layer.

Catalogs tracked financial instruments / portfolio holdings as Egeria data assets,
classified ``Confidential`` — the quant/trading data joins the governed catalog.
Idempotent.

Config-driven: either a portfolio API (``EMERALD_URL`` + ``EMERALD_TOKEN`` →
``/api/portfolios``) or a declared holdings file (``EMERALD_PORTFOLIO`` = JSON list of
``{symbol, name, assetType, account}``). Tolerant — skipped when neither is set.
"""

from __future__ import annotations

import json
import os
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    HTTPX_AVAILABLE = False


def _fetch_api(url: str, token: str | None, verify_ssl: bool) -> list[dict]:
    if not HTTPX_AVAILABLE:
        return []
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    for path in ("/api/portfolios", "/api/positions", "/api/accounts"):
        try:
            with httpx.Client(verify=verify_ssl, timeout=20.0) as c:
                r = c.get(f"{url.rstrip('/')}{path}", headers=headers)
            if r.status_code == 200:
                data = r.json()
                recs = data.get("data") if isinstance(data, dict) else data
                if isinstance(recs, list) and recs:
                    return recs
        except Exception:
            continue
    return []


def _load_file(path: str) -> list[dict]:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return []
    if isinstance(data, dict):
        data = data.get("holdings") or data.get("positions") or []
    return [h for h in data if isinstance(h, dict)] if isinstance(data, list) else []


def harvest_markets(
    api: Any,
    url: str | None = None,
    token: str | None = None,
    *,
    portfolio_path: str | None = None,
    verify_ssl: bool = False,
) -> dict[str, Any]:
    """Catalog financial instruments / holdings into Egeria."""
    report: dict[str, Any] = {"instruments": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    url = url or os.getenv("EMERALD_URL")
    token = token or os.getenv("EMERALD_TOKEN")
    portfolio_path = portfolio_path or os.getenv("EMERALD_PORTFOLIO")
    holdings = _fetch_api(url, token, verify_ssl) if url else []
    if not holdings and portfolio_path and os.path.isfile(portfolio_path):
        holdings = _load_file(portfolio_path)
    if not url and not portfolio_path:
        report["skipped"] = "no markets source (set EMERALD_URL or EMERALD_PORTFOLIO)"
        return report
    report["source"] = {"instruments": len(holdings)}
    if not holdings:
        report["skipped"] = "no holdings returned (unreachable / empty / unauthorized)"
        return report

    store = api.create_asset(
        "SoftwareServer",
        "DataStore::emerald",
        "emerald-exchange",
        description="Emerald Exchange quant/trading store.",
        deployed_implementation_type="Emerald Exchange",
        confidentiality_level=2,
    )
    record_error("store:emerald", store)

    for h in holdings:
        symbol = h.get("symbol") or h.get("ticker") or h.get("name") or h.get("id")
        if not symbol:
            continue
        qn = f"Instrument::Emerald::{symbol}"
        res = api.create_asset(
            "DeployedDatabaseSchema",
            qn,
            str(symbol),
            description=f"Financial instrument/holding '{symbol}'"
            + (f" ({h.get('assetType')})." if h.get("assetType") else "."),
            deployed_implementation_type=h.get("assetType") or "Financial Instrument",
            confidentiality_level=2,
            additional_properties={
                "account": h.get("account"),
                "assetType": h.get("assetType"),
                "source": "Emerald",
            },
        )
        record_error(f"instrument:{symbol}", res)
        report["instruments"].append({"symbol": str(symbol), **res})

    report["summary"] = {
        "instruments": len([i for i in report["instruments"] if i.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
