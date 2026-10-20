"""Validate annotated visual references against current core authority."""

import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree

from tools.contract import safe_file


REQUIRED = {"id", "version", "artwork", "roles", "rules", "states", "accessible_text",
            "viewport", "input_scale", "local_dimensions", "source_hashes"}


def validate_fixture(root: Path, data: dict) -> list[str]:
    errors = []
    for key in sorted(REQUIRED - data.keys()):
        errors.append(f"missing field: {key}")
    if errors:
        return errors
    if not isinstance(data["accessible_text"], str) or not data["accessible_text"].strip():
        errors.append("accessible text missing")
    if not data["roles"] or not data["rules"]:
        errors.append("roles and rules required")
    rules_path = root / "core/rules.json"
    if rules_path.is_file():
        rules_doc = json.loads(rules_path.read_text(encoding="utf-8"))
        ids = {entry["id"] for entry in rules_doc["rules"]}
        errors.extend(f"unknown rule: {rule}" for rule in data["rules"] if rule not in ids)
        if data["version"] != rules_doc.get("version"):
            errors.append("fixture version mismatch")
    try:
        artwork = safe_file(root, data["artwork"])
        if not artwork.is_file():
            errors.append(f"missing artwork: {data['artwork']}")
        else:
            svg = ElementTree.parse(artwork).getroot()
            if not any(tag.tag.endswith("}title") for tag in svg):
                errors.append("artwork has no accessible SVG title")
    except (ValueError, OSError, ElementTree.ParseError) as exc:
        errors.append(f"invalid artwork: {exc}")
    for rel, expected in data["source_hashes"].items():
        try:
            path = safe_file(root, rel)
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                errors.append(f"source hash mismatch: {rel}")
        except ValueError as exc:
            errors.append(f"source hash invalid: {exc}")
    if not isinstance(data["viewport"], dict) or not {"width", "height"} <= data["viewport"].keys():
        errors.append("fixture viewport requires width and height")
    states = data["states"]
    if data["id"] == "state":
        pending = states.get("pending", {})
        observed = states.get("observed", {})
        if pending.get("observed") == "success" or "success" in pending.get("projected", "").lower():
            errors.append("false success in pending state")
        if pending.get("observed") == observed.get("observed"):
            errors.append("pending and observed state are not distinct")
    if data["id"] == "fields":
        field = data.get("field", {})
        if not {"quantity", "range", "neutral", "endpoints", "missing", "legend"} <= field.keys():
            errors.append("field interpretation incomplete")
    if data["id"] == "adaptive":
        orders = data.get("reading_order", {})
        if not orders or len({tuple(v) for v in orders.values()}) != 1:
            errors.append("adaptive reading order changed")
    return errors
