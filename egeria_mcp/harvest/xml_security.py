"""Bounded XML parser shared by governance harvesters."""

from __future__ import annotations

from pathlib import Path

from defusedxml import ElementTree as DefusedET
from defusedxml.common import DefusedXmlException

MAX_XML_BYTES = 32 * 1024 * 1024
MAX_XML_DEPTH = 96
MAX_XML_ELEMENTS = 500_000


class HarvestXmlError(ValueError):
    """An input document crossed a harvester security boundary."""


def parse_xml_root(path: str):
    candidate = Path(path)
    try:
        if candidate.is_symlink() or not candidate.is_file():
            raise HarvestXmlError("harvest input is not a regular file")
        expected = candidate.stat().st_size
        if expected <= 0 or expected > MAX_XML_BYTES:
            raise HarvestXmlError("harvest input exceeds its safe size boundary")
        with candidate.open("rb") as stream:
            payload = stream.read(MAX_XML_BYTES + 1)
    except HarvestXmlError:
        raise
    except OSError:
        raise HarvestXmlError("harvest input is unavailable") from None
    if len(payload) != expected or len(payload) > MAX_XML_BYTES:
        raise HarvestXmlError("harvest input changed while being read")
    try:
        root = DefusedET.fromstring(
            payload,
            forbid_dtd=True,
            forbid_entities=True,
            forbid_external=True,
        )
    except (DefusedET.ParseError, DefusedXmlException, ValueError):
        raise HarvestXmlError("harvest input is invalid") from None

    count = 0
    stack = [(root, 1)]
    while stack:
        element, depth = stack.pop()
        count += 1
        if count > MAX_XML_ELEMENTS or depth > MAX_XML_DEPTH:
            raise HarvestXmlError("harvest input exceeds its structure boundary")
        stack.extend((child, depth + 1) for child in element)
    return root
