"""Security regression coverage for bounded governance XML harvests."""

import pytest

from egeria_mcp.harvest import xml_security


def test_harvester_rejects_dtd(tmp_path):
    document = tmp_path / "input.xml"
    document.write_text(
        '<!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///ignored">]><root>&xxe;</root>',
        encoding="utf-8",
    )
    with pytest.raises(xml_security.HarvestXmlError, match="invalid"):
        xml_security.parse_xml_root(str(document))


def test_harvester_bounds_depth(tmp_path, monkeypatch):
    document = tmp_path / "input.xml"
    document.write_text("<a><b><c><d/></c></b></a>", encoding="utf-8")
    monkeypatch.setattr(xml_security, "MAX_XML_DEPTH", 3)
    with pytest.raises(xml_security.HarvestXmlError, match="structure"):
        xml_security.parse_xml_root(str(document))
