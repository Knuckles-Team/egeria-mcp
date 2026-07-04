"""ARIS / RSA Archer / Odoo harvesters (CONCEPT:EA-KG.domains.bottom-up-harvest-data, CONCEPT:AU-KG.ingest.then-by-its-node).

Asserts the tolerant skip path (no config → skipped, no raise), the asset mapping
+ vendor-neutral capability tag (via monkeypatched fetch, no network), and that
each layer is registered + capability-resolvable for cross-vendor cohorts.
"""

from __future__ import annotations

from egeria_mcp.harvest import archer as archer_mod
from egeria_mcp.harvest import aris as aris_mod
from egeria_mcp.harvest import crm as crm_mod
from egeria_mcp.harvest import odoo as odoo_mod


class FakeApi:
    """Records create_asset/create_collection calls; returns a fake guid."""

    def __init__(self):
        self.assets = []

    def create_asset(self, type_name, qualified_name, display_name, **kw):
        self.assets.append(
            {
                "type_name": type_name,
                "qualifiedName": qualified_name,
                "displayName": display_name,
                **kw,
            }
        )
        return {"guid": f"guid-{len(self.assets)}", "qualifiedName": qualified_name}


# ── skip-when-unconfigured (tolerance) ───────────────────────────────────────
def test_aris_skips_without_config(monkeypatch):
    monkeypatch.delenv("ARIS_URL", raising=False)
    rep = aris_mod.harvest_aris(FakeApi())
    assert "skipped" in rep and not rep["models"]


def test_archer_skips_without_config(monkeypatch):
    monkeypatch.delenv("ARCHER_URL", raising=False)
    rep = archer_mod.harvest_archer(FakeApi())
    assert "skipped" in rep and not rep["records"]


def test_odoo_skips_without_config(monkeypatch):
    monkeypatch.delenv("ODOO_URL", raising=False)
    rep = odoo_mod.harvest_odoo(FakeApi())
    assert "skipped" in rep and not rep["records"]


def test_crm_skips_without_config(monkeypatch):
    monkeypatch.delenv("TWENTY_URL", raising=False)
    monkeypatch.delenv("TWENTY_TOKEN", raising=False)
    rep = crm_mod.harvest_crm(FakeApi())
    assert "skipped" in rep and not rep["records"]


# ── asset mapping + capability tag (monkeypatched fetch) ─────────────────────
def test_aris_catalogs_process_and_architecture(monkeypatch):
    monkeypatch.setenv("ARIS_URL", "https://aris.invalid")
    monkeypatch.setenv("ARIS_TOKEN", "t")
    monkeypatch.setattr(
        aris_mod,
        "fetch_models",
        lambda *a, **k: [
            {"id": "m1", "name": "O2C", "type": "EPC"},
            {"id": "m2", "name": "Landscape", "type": "Application"},
        ],
    )
    api = FakeApi()
    rep = aris_mod.harvest_aris(api)
    caps = {a["additional_properties"]["capability"] for a in api.assets}
    assert caps == {"bpm", "enterprise-architecture"}
    qns = {a["qualifiedName"] for a in api.assets}
    assert "Process::ARIS::m1" in qns
    assert any(q.startswith("ArchiMate::ARIS::") for q in qns)
    assert rep["summary"]["models"] == 2


def test_archer_catalogs_grc(monkeypatch):
    monkeypatch.setenv("ARCHER_URL", "https://archer.invalid")
    monkeypatch.setenv("ARCHER_TOKEN", "t")
    monkeypatch.setattr(
        archer_mod,
        "fetch_records",
        lambda url, token, app, **k: [{"Id": "1", "Name": f"{app}-1"}],
    )
    api = FakeApi()
    archer_mod.harvest_archer(api, applications=["risks", "controls"])
    grc = [
        a for a in api.assets if a["qualifiedName"].startswith("RiskAsset::Archer::")
    ]
    assert len(grc) == 2
    assert all(a["additional_properties"]["capability"] == "grc" for a in grc)


def test_odoo_catalogs_crm(monkeypatch):
    monkeypatch.setenv("ODOO_URL", "https://odoo.invalid")
    monkeypatch.setenv("ODOO_DB", "db")
    monkeypatch.setenv("ODOO_USER", "u")
    monkeypatch.setenv("ODOO_PASSWORD", "p")
    monkeypatch.setattr(odoo_mod, "authenticate", lambda *a, **k: 7)
    monkeypatch.setattr(
        odoo_mod,
        "fetch_records",
        lambda url, db, uid, pw, model, **k: [
            {"id": 1, "display_name": f"{model}-rec"}
        ],
    )
    api = FakeApi()
    odoo_mod.harvest_odoo(api)
    crm = [a for a in api.assets if a["qualifiedName"].startswith("Dataset::Odoo::")]
    assert len(crm) == 2  # res.partner + crm.lead
    assert all(a["additional_properties"]["capability"] == "crm" for a in crm)


def test_crm_catalogs_twenty(monkeypatch):
    monkeypatch.setenv("TWENTY_URL", "https://twenty.invalid")
    monkeypatch.setenv("TWENTY_TOKEN", "t")
    monkeypatch.setattr(
        crm_mod,
        "_fetch",
        lambda url, token, prefix, resource, verify_ssl: (
            [{"id": "c1", "name": "Acme"}]
            if resource == "companies"
            else [{"id": "p1", "name": {"firstName": "Jane", "lastName": "Doe"}}]
        ),
    )
    api = FakeApi()
    rep = crm_mod.harvest_crm(api)
    records = [
        a for a in api.assets if a["qualifiedName"].startswith("Dataset::Twenty::")
    ]
    assert len(records) == 2  # Company + Person
    assert all(a["additional_properties"]["source"] == "Twenty" for a in records)
    assert {"Company", "Person"} == {
        a["additional_properties"]["crmObject"] for a in records
    }
    assert "Dataset::Twenty::Company::c1" in {a["qualifiedName"] for a in records}
    assert rep["source"]["records"] == 2


# ── registry + capability resolution (cross-vendor cohorts) ──────────────────
def test_layers_registered():
    from egeria_mcp.harvest.runner import LAYERS

    assert {"aris", "archer", "odoo", "crm"} <= set(LAYERS)


def test_capability_resolution_for_cohorts():
    from egeria_mcp.reconcile import _capability_of

    # Odoo + Twenty resolve to the same 'crm' cohort (cross-vendor consolidation).
    assert _capability_of({"qualifiedName": "Dataset::Odoo::Customer::1"}) == "crm"
    assert _capability_of({"qualifiedName": "Dataset::Twenty::Company::1"}) == "crm"
    assert _capability_of({"qualifiedName": "RiskAsset::Archer::Risk::1"}) == "grc"
    assert _capability_of({"additionalProperties": {"source": "ARIS"}}) == "bpm"
