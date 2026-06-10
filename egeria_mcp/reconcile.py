"""Cross-layer reconciliation — weave the 34 harvest layers into one graph.

Each harvest layer catalogs its source into Egeria independently. This pass connects
those islands: it scans the catalog, matches assets that refer to the same real thing
or have a real dependency across layers, and creates ``DataFlow`` edges (with a
semantic label) so the whole estate becomes one traversable lineage/governance graph
— and so ``governed_route``'s downstream-impact sees cross-layer dependencies.

The matchers (see ``PATTERNS``) are deterministic and conservative; linking is
idempotent — each source's existing lineage is read once and already-connected
targets are skipped. Confidentiality is propagated up hosting chains (a store that
hosts Confidential data is raised to at least that level).

Entry point: :func:`reconcile`.
"""

from __future__ import annotations

import json as _json
from typing import Any

PATTERNS = (
    "host-hosting",
    "service-store",
    "dataset-store",
    "source-store",
    "ingress-exposure",
    "monitoring",
    "cmdb-identity",
    "access-control",
    "repo-service",
    "datasource-store",
    "ea-realization",
    "semantic-assignment",
    "capability-cohort",
    "cross-vendor-identity",
    "confidentiality-propagation",
)

# Canonical capability per asset, derived from its source / qualifiedName when not
# tagged explicitly (additionalProperties.capability). Used to cross-link
# same-capability assets across first-party and open-source vendors.
_CAP_BY_SOURCE = {
    "ServiceNow": "ITSM",
    "LeanIX": "enterprise-architecture",
    "ArchiMate": "enterprise-architecture",
    "GitLab": "vcs",
    "GitHub": "vcs",
    "Camunda": "bpm",
    "Ansible": "bpm",
    "Confluence": "knowledge",
    "Nextcloud": "knowledge",
    "Jira": "pm",
    "Plane": "pm",
    # First-party EA+BPM / GRC / CRM suites + their open-source cohort peers.
    "ARIS": "bpm",
    "Archer": "grc",
    "Twenty": "crm",
    "Odoo": "crm",
}
_CAP_BY_PREFIX = {
    "CI::ServiceNow::": "ITSM",
    "Repository::": "vcs",
    "FactSheet::": "enterprise-architecture",
    "ArchiMate::": "enterprise-architecture",
    "Process::Camunda::": "bpm",
    "Process::Ansible::": "bpm",
    "Process::ARIS::": "bpm",
    "RiskAsset::Archer::": "grc",
    "Dataset::Twenty::": "crm",
    "Dataset::Odoo::": "crm",
}


def _capability_of(rec: dict) -> str | None:
    """Canonical capability for an asset (explicit tag → source → qn prefix).

    CONCEPT:EG-009 — Vendor-Neutral Capability Tagging. Resolves the canonical
    ``capability`` so first-party and open-source adapters of the same capability
    cross-link through a shared ``Capability::<cap>`` cohort.
    """
    ap = rec.get("additionalProperties") or {}
    if ap.get("capability"):
        return str(ap["capability"]).lower()
    if ap.get("source") in _CAP_BY_SOURCE:
        return _CAP_BY_SOURCE[ap["source"]].lower()
    qn = rec.get("qualifiedName") or ""
    for pre, cap in _CAP_BY_PREFIX.items():
        if qn.startswith(pre):
            return cap.lower()
    return None


def _source_of(rec: dict) -> str:
    ap = rec.get("additionalProperties") or {}
    return ap.get("source") or (rec.get("qualifiedName") or "").split("::")[0]


# qualifiedName prefixes the harvest layers use, grouped by role.
_PREFIXES = {
    "nodes": ["Node::", "Host::"],
    "stores": ["DataStore::"],
    "datasets": [
        "Dataset::",
        "Instrument::",
        "Topic::",
        "Content::",
        "Snapshot::",
        "Model::",
    ],
    "services": ["Service::"],
    "routes": ["Route::"],
    "monitors": ["Monitor::"],
    "cis": ["CI::ServiceNow::"],
    "clients": ["Client::"],
    "repos": ["Repository::"],
    "datasources": ["Datasource::"],
    "ea": ["ArchiMate::", "FactSheet::"],
}

# additionalProperties.source value → the DataStore::<name> it belongs to.
_SOURCE_STORE = {
    "Kafka": "kafka",
    "Qdrant": "qdrant",
    "Jena": "fuseki",
    "Firefly-III": "firefly",
    "Twenty": "twenty",
    "ERPNext": "erpnext-db",
    "Emerald": "emerald",
    "Home Assistant": "homeassistant",
}


def _paginated_search(api: Any, term: str, *, max_total: int = 1000) -> list[dict]:
    """Page through the asset-catalog by-search-string for one term."""
    out: list[dict] = []
    start = 0
    page = 100
    try:
        tok = api._bearer()
    except Exception:
        return out
    url = api._omvs("asset-catalog", "assets/in-domain/by-search-string")
    while len(out) < max_total:
        try:
            r = api._http().post(
                f"{url}?startFrom={start}&pageSize={page}",
                headers={
                    "Authorization": f"Bearer {tok}",
                    "Content-Type": "application/json",
                },
                content=_json.dumps(
                    {
                        "class": "SearchStringRequestBody",
                        "searchString": term,
                        "ignoreCase": True,
                    }
                ),
            )
        except Exception:
            break
        if r.status_code != 200:
            break
        batch = api._elements(r)
        if not batch:
            break
        out.extend(batch)
        if len(batch) < page:
            break
        start += page
    return out


def _load(api: Any) -> dict[str, list[dict]]:
    """Load catalogued assets by role (deduped by GUID)."""
    loaded: dict[str, list[dict]] = {}
    for role, prefixes in _PREFIXES.items():
        seen: dict[str, dict] = {}
        for pre in prefixes:
            for rec in _paginated_search(api, pre):
                qn = rec.get("qualifiedName") or ""
                g = rec.get("guid")
                if g and qn.startswith(pre) and g not in seen:
                    seen[g] = rec
        loaded[role] = list(seen.values())
    return loaded


def _connected(api: Any, guid: str) -> set[str]:
    """GUIDs already linked to ``guid`` via lineage (for idempotency)."""
    out: set[str] = set()
    lin = api.lineage(guid) or {}
    for edge in lin.get("lineageLinkage") or []:
        rel = edge.get("relatedElement") or {}
        hdr = rel.get("elementHeader") if isinstance(rel, dict) else None
        gg = (hdr or {}).get("guid") if isinstance(hdr, dict) else rel.get("guid")
        if gg:
            out.add(gg)
    return out


def _core(qn: str, prefix: str) -> str:
    return qn[len(prefix) :] if qn.startswith(prefix) else qn


def reconcile(api: Any, *, propagate_confidentiality: bool = True) -> dict[str, Any]:
    """Cross-link the catalogue across layers; return a per-pattern report.

    CONCEPT:EG-006 — Cross-Layer Reconciliation. Weaves the independently-harvested
    layers into one graph via deterministic matchers that create labelled
    ``DataFlow`` edges and propagate confidentiality up hosting chains. Idempotent;
    makes ``governed_route`` cross-layer- and cross-vendor-aware.
    """
    if not getattr(api, "enable_write", False):
        return {"error": "writes disabled — set EGERIA_ENABLE_WRITE=true"}

    assets = _load(api)
    nodes = assets["nodes"]
    stores = assets["stores"]
    datasets = assets["datasets"]
    services = assets["services"]
    routes = assets["routes"]
    monitors = assets["monitors"]
    cis = assets["cis"]
    clients = assets["clients"]
    repos = assets["repos"]
    datasources = assets["datasources"]
    ea = assets["ea"]

    report: dict[str, Any] = {p: {"links": 0, "items": []} for p in PATTERNS}
    report["loaded"] = {k: len(v) for k, v in assets.items()}
    cache: dict[str, set[str]] = {}

    def link(src: dict, tgt: dict, label: str, pattern: str) -> None:
        sg, tg = src.get("guid"), tgt.get("guid")
        if not sg or not tg or sg == tg:
            return
        if sg not in cache:
            cache[sg] = _connected(api, sg)
        if tg in cache[sg]:
            return
        res = api.link_data_flow(sg, tg, label=label)
        if isinstance(res, dict) and not res.get("error"):
            cache[sg].add(tg)
            report[pattern]["links"] += 1
            report[pattern]["items"].append(
                f"{src.get('qualifiedName')} →[{label}] {tgt.get('qualifiedName')}"
            )

    node_by_name = {
        _core(n["qualifiedName"], "Node::").split("::")[0]
        if n["qualifiedName"].startswith("Node::")
        else _core(n["qualifiedName"], "Host::"): n
        for n in nodes
    }
    store_by_name = {_core(s["qualifiedName"], "DataStore::"): s for s in stores}

    # P1 host-hosting: asset.hostNode → Node hosts asset
    for pool in (stores, datasets, services):
        for a in pool:
            host = (a.get("additionalProperties") or {}).get("hostNode")
            if host and host in node_by_name:
                link(node_by_name[host], a, "hosts", "host-hosting")

    # P2 / address: store.networkAddress host → node by addr (best-effort, skipped if no match)

    # P3 service-store identity: Service::*_<name> realizes DataStore::<name>
    for svc in services:
        sname = _core(svc["qualifiedName"], "Service::")
        for store_name, store in store_by_name.items():
            if (
                sname == store_name
                or sname.endswith("_" + store_name)
                or store_name in sname.split("_")
            ):
                link(svc, store, "realizes", "service-store")
                break

    # P4 dataset-store containment: Dataset::<store>::* hosted by DataStore::<store>
    for ds in datasets:
        qn = ds["qualifiedName"]
        if qn.startswith("Dataset::") and qn.count("::") >= 2:
            parent = qn.split("::")[1].split(".")[0]
            match_store = store_by_name.get(parent)
            if match_store:
                link(match_store, ds, "hosts", "dataset-store")

    # P11 source-store: data asset → its source DataStore (by `source` property)
    for ds in datasets:
        source = (ds.get("additionalProperties") or {}).get("source")
        match_store = (
            store_by_name.get(_SOURCE_STORE.get(source, "")) if source else None
        )
        if match_store:
            link(match_store, ds, "hosts", "source-store")

    # P5 ingress-exposure: Route.upstream → Service
    svc_by_name = {_core(s["qualifiedName"], "Service::"): s for s in services}
    for rt in routes:
        up = (rt.get("additionalProperties") or {}).get("upstream") or ""
        host = up.split(":")[0].split("/")[0]
        if not host:
            continue
        for sname, svc in svc_by_name.items():
            if host == sname or sname.endswith("_" + host) or host in sname.split("_"):
                link(rt, svc, "routes-to", "ingress-exposure")
                break

    # P6 monitoring: Monitor.name ~ Route/Service/Node/Store
    targets_by_name = {
        **store_by_name,
        **svc_by_name,
        **{_core(n["qualifiedName"], "Node::"): n for n in nodes},
        **{_core(r["qualifiedName"], "Route::"): r for r in routes},
    }
    for mon in monitors:
        mname = _core(mon["qualifiedName"], "Monitor::").lower()
        for tname, tgt in targets_by_name.items():
            if mname and (mname in tname.lower() or tname.lower().endswith(mname)):
                link(mon, tgt, "monitors", "monitoring")
                break

    # P7 cmdb-identity: CI::ServiceNow::<name> ~ infra asset
    infra_by_name = {
        **store_by_name,
        **{_core(n["qualifiedName"], "Node::"): n for n in nodes},
        **svc_by_name,
    }
    for ci in cis:
        cname = _core(ci["qualifiedName"], "CI::ServiceNow::")
        for iname, tgt in infra_by_name.items():
            if cname and cname.lower() == iname.lower():
                link(ci, tgt, "same-as", "cmdb-identity")
                break

    # P8 access-control: Keycloak Client::<realm>::<id> secures matching Service
    for cl in clients:
        parts = _core(cl["qualifiedName"], "Client::").split("::")
        cid = parts[-1] if parts else ""
        for sname, svc in svc_by_name.items():
            if cid and (cid == sname or cid in sname.split("_")):
                link(cl, svc, "secures", "access-control")
                break

    def _repo_name(r: dict) -> str:
        return (
            _core(r["qualifiedName"], "Repository::")
            .split("::")[-1]
            .split("/")[-1]
            .lower()
        )

    # P12 repo-service: a Repository deploys the Service that runs its build
    for repo in repos:
        rname = _repo_name(repo)
        for sname, svc in svc_by_name.items():
            sl = sname.lower()
            if rname and (
                rname == sl or sl.endswith("_" + rname) or rname in sl.split("_")
            ):
                link(repo, svc, "deploys", "repo-service")
                break

    # P16 datasource-store: a Grafana datasource reads a DataStore (by name)
    for dsrc in datasources:
        dname = _core(dsrc["qualifiedName"], "Datasource::").split("::")[-1].lower()
        for store_name, store in store_by_name.items():
            if dname and (dname == store_name.lower() or store_name.lower() in dname):
                link(dsrc, store, "reads", "datasource-store")
                break

    # P21 ea-realization: ArchiMate/LeanIX element → the running asset it models
    real_by_name: dict[str, dict] = {}
    real_by_name.update(
        {_core(s["qualifiedName"], "Service::").lower(): s for s in services}
    )
    real_by_name.update(
        {_core(s["qualifiedName"], "DataStore::").lower(): s for s in stores}
    )
    real_by_name.update({_repo_name(r): r for r in repos})
    for el in ea:
        name = (el.get("displayName") or "").lower()
        if not name:
            continue
        target = real_by_name.get(name)
        if not target:
            for rn, ra in real_by_name.items():
                if rn and (name == rn or rn.endswith(name) or name in rn.split("_")):
                    target = ra
                    break
        if target:
            link(el, target, "realized-by", "ea-realization")

    # P9 semantic-assignment: asset.displayName == Glossary Term → means Concept
    terms = {
        t.get("displayName"): t
        for t in _paginated_search(api, "Term::")
        if t.get("displayName")
    }
    if terms:
        for pool in (datasets, services, stores):
            for a in pool:
                term = terms.get(a.get("displayName"))
                if term:
                    link(a, term, "means", "semantic-assignment")

    # Capability cohorts + cross-vendor identity: group assets that serve the SAME
    # capability across DIFFERENT vendors (first-party + open-source). Only build a
    # cohort where ≥2 distinct sources are present, so it stays bounded and meaningful
    # (e.g. ITSM = ServiceNow + ERPNext; vcs = GitLab + GitHub; EA = LeanIX + ArchiMate).
    cap_groups: dict[str, list[dict]] = {}
    cap_sources: dict[str, set[str]] = {}
    for rec in (r for pool in assets.values() for r in pool):
        cap = _capability_of(rec)
        if not cap:
            continue
        cap_groups.setdefault(cap, []).append(rec)
        cap_sources.setdefault(cap, set()).add(_source_of(rec))

    for cap, recs in cap_groups.items():
        if len(cap_sources[cap]) < 2:
            continue  # single-vendor — nothing cross-vendor to link
        col = api.create_collection(
            f"Capability {cap}",
            description=f"All {cap} assets across first-party + open-source vendors.",
            category="Capability",
        )
        if col.get("guid"):
            cohort = {"guid": col["guid"], "qualifiedName": f"Capability::{cap}"}
            for rec in recs:
                link(cohort, rec, "groups", "capability-cohort")
        # cross-vendor identity: same displayName from different sources = same entity
        by_name: dict[str, list[dict]] = {}
        for rec in recs:
            nm = (rec.get("displayName") or "").lower()
            if nm:
                by_name.setdefault(nm, []).append(rec)
        for grp in by_name.values():
            if len(grp) < 2 or len({_source_of(g) for g in grp}) < 2:
                continue
            for other in grp[1:]:
                link(grp[0], other, "same-as", "cross-vendor-identity")

    # P10 confidentiality-propagation: raise a store to the max of its datasets' levels
    if propagate_confidentiality:
        for ds in datasets:
            qn = ds["qualifiedName"]
            if not (qn.startswith("Dataset::") and qn.count("::") >= 2):
                continue
            match_store = store_by_name.get(qn.split("::")[1].split(".")[0])
            if not match_store:
                continue
            ds_level = api.governance_for(ds["guid"]).get("confidentialityLevel")
            st_level = api.governance_for(match_store["guid"]).get(
                "confidentialityLevel"
            )
            if isinstance(ds_level, int) and (
                not isinstance(st_level, int) or ds_level > st_level
            ):
                api.set_confidentiality(match_store["guid"], ds_level)
                report["confidentiality-propagation"]["links"] += 1
                report["confidentiality-propagation"]["items"].append(
                    f"{match_store['qualifiedName']} → level {ds_level} (from {ds['qualifiedName']})"
                )

    report["summary"] = {p: report[p]["links"] for p in PATTERNS}
    report["summary"]["total_links"] = sum(report[p]["links"] for p in PATTERNS)
    return report
