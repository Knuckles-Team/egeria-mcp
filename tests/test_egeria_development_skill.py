"""Keep the Egeria development skill bound to the connector contract."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "egeria_mcp" / "skills" / "egeria-mcp-development" / "SKILL.md"


@pytest.mark.spec("PIPE-CONNSPEC-R117.4")
def test_egeria_development_skill_describes_the_supported_delivery_contract():
    text = SKILL.read_text(encoding="utf-8")
    frontmatter = text.split("---", 2)[1]
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    init = (ROOT / "egeria_mcp" / "__init__.py").read_text(encoding="utf-8")
    auth = (ROOT / "egeria_mcp" / "auth.py").read_text(encoding="utf-8")
    api = (ROOT / "egeria_mcp" / "api_client.py").read_text(encoding="utf-8")
    tools = (ROOT / "egeria_mcp" / "mcp" / "mcp_egeria.py").read_text(encoding="utf-8")
    sources = (ROOT / "egeria_mcp" / "connector_sources.py").read_text(encoding="utf-8")

    assert SKILL.is_file()
    assert re.search(r"^name:\s*egeria-mcp-development\s*$", frontmatter, re.M)
    assert re.search(r"^skill_type:\s*skill\s*$", frontmatter, re.M)
    assert "## Rapid delivery: the 5-minute contract" in text
    for term in (
        "egeria_mcp/__init__.py",
        "egeria_mcp/api_client.py",
        "egeria_mcp/api/api_client_egeria.py",
        "egeria_mcp/auth.py",
        "egeria_mcp/mcp/mcp_egeria.py",
        "egeria_mcp/connector_sources.py",
        "egeria_mcp/harvest/",
        "egeria_mcp/ontology/",
        "EGERIA_PLATFORM_URL",
        "EGERIA_VIEW_SERVER",
        "EGERIA_USER",
        "EGERIA_USER_PASSWORD",
        "EGERIA_TLS_PROFILE",
        "EGERIA_ENABLE_WRITE",
        "egeria_lineage_scan",
        "egeria_governed_route",
        "egeria_harvest",
        "egeria_reconcile",
        "egeria_ingest_catalog",
        "connector://resources",
        "skills/**",
        "python_pipeline.yml@main",
        "connector: true",
        "container_pipeline.yml@main",
        "render_connector: true",
        "pages_pipeline.yml@main",
        "uv run --locked --extra test pytest",
    ):
        assert term in text

    assert "verify=False" not in text
    assert "--no-verify" not in text
    assert "EGERIA_VERIFY_SSL" not in text
    assert '"skills/**"' in pyproject
    assert 'egeria-mcp = "egeria_mcp:connector"' in pyproject
    assert "Connector" in init
    assert "EgeriaApi" in api
    assert "EGERIA_PLATFORM_URL" in auth
    assert "EGERIA_ENABLE_WRITE" in tools
    assert "source_meta" in sources
