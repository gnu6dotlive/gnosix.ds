"""Authority, path, digest, and evidence checks for a V03 package."""

import argparse
import hashlib
import json
from pathlib import Path


CLASSES = {"core", "reference", "profile", "evidence"}
STATUSES = {"specified", "mapped", "rendered", "verified"}


def safe_file(root: Path, rel: str) -> Path:
    path = (root / rel).resolve()
    root = root.resolve()
    if Path(rel).is_absolute() or path == root or root not in path.parents:
        raise ValueError(f"unsafe path: {rel}")
    return path


def contract_digest(root: Path, paths: list[str]) -> str:
    records = []
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate digest path")
    for rel in sorted(paths):
        content_hash = hashlib.sha256(safe_file(root, rel).read_bytes()).hexdigest()
        records.append(f"{rel}\0{content_hash}\n")
    return hashlib.sha256("".join(records).encode("utf-8")).hexdigest()


def manifest_digest_paths(manifest: dict) -> list[str]:
    paths = []
    for item in manifest.get("files", []):
        if not isinstance(item, dict):
            continue
        rel = item.get("path")
        if not isinstance(rel, str):
            continue
        if item.get("class") == "core" or (item.get("class") == "reference" and rel.endswith(".json")):
            paths.append(rel)
    return paths


def validate_package(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"manifest unreadable: {exc}"]
    files = manifest.get("files", [])
    if not isinstance(files, list):
        return ["manifest files must be a list"]
    paths: set[str] = set()
    digest_paths = manifest_digest_paths(manifest)
    for item in files:
        if not isinstance(item, dict):
            errors.append("manifest entry must be an object")
            continue
        rel = item.get("path")
        if not isinstance(rel, str) or not rel:
            errors.append("manifest path missing")
            continue
        if rel in paths:
            errors.append(f"duplicate file: {rel}")
        paths.add(rel)
        if item.get("class") not in CLASSES:
            errors.append(f"invalid class: {rel}")
        try:
            path = safe_file(root, rel)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not path.is_file():
            errors.append(f"missing file: {rel}")
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != item.get("sha256"):
            errors.append(f"hash mismatch: {rel}")
    expected_digest = manifest.get("contract_digest")
    if expected_digest and not any("missing file" in e or "unsafe path" in e for e in errors):
        try:
            if contract_digest(root, digest_paths) != expected_digest:
                errors.append("contract digest mismatch")
        except (OSError, ValueError) as exc:
            errors.append(f"contract digest invalid: {exc}")
    rules_path = root / "core/rules.json"
    if rules_path.is_file():
        try:
            rules = json.loads(rules_path.read_text(encoding="utf-8"))["rules"]
            ids = [rule["id"] for rule in rules]
            if len(ids) != len(set(ids)):
                errors.append("duplicate rule id")
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"rules invalid: {exc}")
    fixture_ids = []
    for path in sorted((root / "references").glob("*.json")):
        try:
            fixture_ids.append(json.loads(path.read_text(encoding="utf-8"))["id"])
        except (KeyError, ValueError) as exc:
            errors.append(f"fixture invalid: {path.name}: {exc}")
    if len(fixture_ids) != len(set(fixture_ids)):
        errors.append("duplicate fixture id")
    for path in sorted((root / "profiles").glob("*/status.json")):
        try:
            status = json.loads(path.read_text(encoding="utf-8"))
            if status.get("status") not in STATUSES:
                errors.append(f"invalid status: {path.parent.name}")
            if status.get("status") == "verified" and not status.get("evidence"):
                errors.append(f"verified requires evidence: {path.parent.name}")
        except ValueError as exc:
            errors.append(f"invalid status file: {path}: {exc}")
    return errors


def cli(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate gnosix_DS package integrity and contract digest.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate", metavar="ROOT", help="validate the package rooted at ROOT")
    mode.add_argument("--digest", metavar="ROOT", help="print the computed contract digest for ROOT")
    args = parser.parse_args(argv)

    if args.validate:
        root = Path(args.validate)
        errors = validate_package(root)
        if errors:
            for error in errors:
                print(error)
            return 1
        print("PASS")
        return 0

    root = Path(args.digest)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    print(contract_digest(root, manifest_digest_paths(manifest)))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
