"""Shared report bookkeeping for harvest connectors.

Every harvest connector builds the same small ``report`` shape (a dict of
per-resource-type lists plus an ``"errors"`` list) and needs the same two bits of
bookkeeping around each ``api.create_asset``/``api.create_collection`` call: record
an error if the call failed, and count how many calls actually produced an asset
(``guid`` present) for the final ``summary``. Pulled out once so every connector's
per-resource-type loop stays focused on its own mapping logic instead of repeating
this boilerplate — no business logic lives here.
"""

from __future__ import annotations

from typing import Any


def note_error(report: dict[str, Any], item: str, result: Any) -> None:
    """Append ``{"item": item, "error": ...}`` to ``report["errors"]`` on failure."""
    if isinstance(result, dict) and result.get("error"):
        report["errors"].append({"item": item, "error": result["error"]})


def count_created(entries: list[dict]) -> int:
    """Count report entries that carry a ``guid`` (the create call succeeded)."""
    return len([e for e in entries if e.get("guid")])
