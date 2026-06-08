"""Document-store harvest — the DocumentDB / MongoDB layer.

Catalogs databases as Egeria ``RelationalDatabase`` assets and their collections as
``DeployedDatabaseSchema`` datasets, anchored to the store. Idempotent.

Config-driven (``MONGODB_URI``); tolerant. Uses ``pymongo`` if available (optional
dependency) — skipped cleanly otherwise.
"""

from __future__ import annotations

import os
from typing import Any

_SYSTEM_DBS = {"admin", "local", "config"}


def _resolve(uri: str | None) -> str | None:
    if uri:
        return uri
    direct = os.getenv("MONGODB_URI")
    if direct:
        return direct
    host = os.getenv("MONGODB_HOST")
    if host:
        return f"mongodb://{host}:{os.getenv('MONGODB_PORT', '27017')}"
    return None


def harvest_documentdb(api: Any, uri: str | None = None) -> dict[str, Any]:
    """Catalog MongoDB/DocumentDB databases + collections into Egeria."""
    report: dict[str, Any] = {"databases": [], "collections": [], "errors": []}

    def record_error(what: str, res: dict) -> None:
        if isinstance(res, dict) and res.get("error"):
            report["errors"].append({"item": what, "error": res["error"]})

    uri = _resolve(uri)
    if not uri:
        report["skipped"] = "no MongoDB URI (set MONGODB_URI)"
        return report
    try:
        from pymongo import MongoClient
    except Exception:
        report["skipped"] = "pymongo not installed (pip install pymongo)"
        return report

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        db_names = [d for d in client.list_database_names() if d not in _SYSTEM_DBS]
    except Exception as exc:
        report["skipped"] = f"connection failed: {str(exc)[:80]}"
        return report

    report["source"] = {"databases": len(db_names)}
    for dbname in db_names:
        dres = api.create_asset(
            "RelationalDatabase",
            f"Dataset::Mongo::{dbname}",
            dbname,
            description=f"MongoDB database '{dbname}'.",
            deployed_implementation_type="MongoDB Database",
            confidentiality_level=2,
        )
        record_error(f"db:{dbname}", dres)
        report["databases"].append({"name": dbname, **dres})
        try:
            colls = client[dbname].list_collection_names()
        except Exception:
            colls = []
        for coll in colls:
            qn = f"Dataset::Mongo::{dbname}.{coll}"
            res = api.create_asset(
                "DeployedDatabaseSchema",
                qn,
                coll,
                description=f"MongoDB collection '{dbname}.{coll}'.",
                deployed_implementation_type="MongoDB Collection",
                confidentiality_level=2,
                additional_properties={"database": dbname, "source": "MongoDB"},
            )
            record_error(f"collection:{dbname}.{coll}", res)
            report["collections"].append({"name": f"{dbname}.{coll}", **res})

    report["summary"] = {
        "databases": len([d for d in report["databases"] if d.get("guid")]),
        "collections": len([c for c in report["collections"] if c.get("guid")]),
        "errors": len(report["errors"]),
    }
    return report
