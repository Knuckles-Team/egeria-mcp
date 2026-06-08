"""Governance-aware routing — the federation delivering a decision (KG-2.9).

This is the "so what" of the Egeria↔KG federation: before a workflow acts on a
data asset, it consults Egeria (the metadata system-of-record) for the asset's
governance classifications and downstream data lineage, and returns a routing
decision the orchestrator can enforce — proceed, require approval, or treat as
impact-bearing. Egeria provides the metadata model the workflow *references*; it
does not orchestrate.

Wire point: this maps onto the agent-utilities ``policy`` routing strategy
(``graph/routing/strategies/policy``) — a governed step calls :func:`governed_route`
and the strategy denies / escalates / sequences accordingly.
"""

from __future__ import annotations

from typing import Any

# Egeria Confidentiality scale: 0 Unclassified, 1 Internal, 2 Confidential,
# 3 Sensitive, 4 Restricted. At/above this level a workflow needs approval.
_APPROVAL_LEVEL = 2

# Classification names (case-insensitive substrings) that gate routing on their
# mere presence, independent of any numeric level (e.g. a Retention hold).
_GATING_CLASSIFICATIONS = ("retention", "criticality")


def governed_route(api: Any, asset_guid: str) -> dict[str, Any]:
    """Return a policy-aware routing decision for acting on an Egeria asset.

    Parameters
    ----------
    api:
        An ``EgeriaApi`` (or duck-typed client) exposing ``governance_for`` and
        ``lineage``.
    asset_guid:
        The Egeria GUID of the data asset about to be acted on.

    Returns
    -------
    dict with ``decision`` in {``proceed``, ``require_approval``, ``review``},
    the governing ``classifications``, downstream lineage ``impact`` count, and
    human-readable ``reasons``.
    """
    gov = api.governance_for(asset_guid) or {}
    lin = api.lineage(asset_guid) or {}

    classifications = gov.get("classifications") or []
    conf_level = gov.get("confidentialityLevel")
    classified_restricted = (
        isinstance(conf_level, int) and conf_level >= _APPROVAL_LEVEL
    )
    # A gating classification (Retention/Criticality) escalates on presence alone.
    gating = [
        c
        for c in classifications
        if any(g in str(c.get("name", c)).lower() for g in _GATING_CLASSIFICATIONS)
    ]
    if gating:
        classified_restricted = True

    # Downstream lineage = consumers impacted by a change to this asset. Egeria's
    # AssetLineageGraph carries connected edges in ``lineageLinkage``.
    impact = 0
    for key in ("lineageLinkage", "lineageRelationships", "nodes", "elements", "edges"):
        val = lin.get(key)
        if isinstance(val, list):
            impact = max(impact, len(val))

    _LEVEL_NAMES = {
        0: "Unclassified",
        1: "Internal",
        2: "Confidential",
        3: "Sensitive",
        4: "Restricted",
    }

    reasons: list[str] = []
    decision = "proceed"
    if classified_restricted:
        decision = "require_approval"
        if isinstance(conf_level, int):
            reasons.append(
                f"Confidentiality={_LEVEL_NAMES.get(conf_level, conf_level)} "
                f"(level {conf_level}) — approval required"
            )
        if gating:
            names = ", ".join(sorted({str(c.get("name", c)) for c in gating}))
            reasons.append(
                f"gating classification(s) present ({names}) — approval required"
            )
    if impact > 0:
        if decision == "proceed":
            decision = "review"
        reasons.append(
            f"{impact} downstream lineage element(s) — sequence change with impact awareness"
        )
    if not reasons:
        reasons.append(
            "no governance restrictions and no downstream lineage — safe to proceed"
        )

    return {
        "asset_guid": asset_guid,
        "decision": decision,
        "reasons": reasons,
        "classifications": classifications,
        "confidentialityLevel": conf_level,
        "downstream_impact": impact,
    }
