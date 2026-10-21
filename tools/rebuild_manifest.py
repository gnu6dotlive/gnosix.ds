"""Rebuild manifest.json file hashes and the contract digest.

The package treats manifest.json as the authority for what exists and what each
file hashes to. Adding or editing a file without regenerating it here makes
`contract.py --validate` fail, which is the intended behaviour but an annoying
way to discover a new file. This regenerates the manifest in place, preserving
the existing class of every file already listed and inferring a class for new
ones.

    python tools/rebuild_manifest.py
    python tools/rebuild_manifest.py --check   # report drift, change nothing
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Running this file as a script puts tools/ on sys.path, not the package root,
# so `from tools.contract import ...` fails with a ModuleNotFoundError. The
# README tells the reader to run this file as a script, and it did not work:
# the documented command was the one invocation that could not run. Putting
# the package root on the path first makes both forms work.
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from tools.contract import CLASSES, contract_digest, manifest_digest_paths, safe_file

DEFAULT_CLASS = "evidence"
PROFILE_PREFIX = "profiles/"
CORE_PREFIX = "core/"


def infer_class(rel: str) -> str:
    """Classify a path the way the existing manifest does."""
    if rel.startswith(CORE_PREFIX) or rel.startswith("assets/fonts/") or rel.startswith("assets/identity/"):
        return "core"
    if rel.startswith(PROFILE_PREFIX):
        return "profile"
    if rel.startswith("references/") or rel.startswith("research/"):
        return "reference"
    return DEFAULT_CLASS


def iter_package_files(root: Path) -> list[str]:
    # "dist" holds the distributable archive that this very script's package
    # is built into. A build output that hashes itself into the manifest it
    # is built from would make the manifest depend on whether the archive
    # happened to exist.
    #
    # ".github" is the CI configuration, "ci" is the local simulation of it
    # and "figcraft" is the FigCraft projection. None of them is package
    # content: they describe how the repository is built and consumed, and
    # the package is the thing that is built. The manifest describes the
    # package, so a file the package does not carry is not a file the
    # manifest hashes.
    # "target" is the Rust build output of the native projection, and a
    # build output is never package content.
    skip_dirs = {".git", "__pycache__", ".pytest_cache", ".venv", "node_modules", ".DS_Store", "dist", ".github", "figcraft", "handoff", "target", ".ci-cache"}

    # The local release proof is a record of what was proved on this machine,
    # not part of the package. The local simulation of the runner is the
    # same: it is how the machine proves the run, not what the run is. The
    # document that says what each gate must say is neither, and it travels.
    skip_files = {".release-proof.json", "local-ci.sh", "pre-push.sh",
                  "provision-engine.sh", "provision-browser.sh"}
    out = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        # The ignored names are judged on the path *inside* the package. A
        # copy of the package that sits in a directory called node_modules
        # would otherwise ignore itself, and every file in it would look
        # like a file that was dropped.
        relative_parts = path.relative_to(root).parts
        if any(part in skip_dirs for part in relative_parts):
            continue
        if path.name in skip_files:
            continue
        if path.name == "manifest.json":
            continue
        out.append(str(path.relative_to(root)))
    return out


def build(root: Path) -> dict:
    manifest_path = root / "manifest.json"
    existing = json.loads(manifest_path.read_text(encoding="utf-8"))
    prior = {item["path"]: item for item in existing.get("files", [])}

    files = []
    for rel in iter_package_files(root):
        previous = prior.get(rel)
        klass = previous["class"] if previous and previous.get("class") in CLASSES else infer_class(rel)
        digest = hashlib.sha256(safe_file(root, rel).read_bytes()).hexdigest()
        files.append({"class": klass, "path": rel, "sha256": digest})

    dropped = sorted(set(prior) - {item["path"] for item in files})
    for rel in dropped:
        print(f"  dropped (no longer present): {rel}")

    rebuilt = dict(existing)
    rebuilt["files"] = files
    rebuilt["contract_digest"] = contract_digest(root, manifest_digest_paths(rebuilt))
    return rebuilt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    args = parser.parse_args()

    current = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    rebuilt = build(ROOT)

    added = sorted({i["path"] for i in rebuilt["files"]} - {i["path"] for i in current["files"]})
    changed = sorted(
        item["path"] for item in rebuilt["files"]
        if any(p["path"] == item["path"] and p["sha256"] != item["sha256"] for p in current["files"])
    )
    for rel in added:
        print(f"  added:   {rel}")
    for rel in changed:
        print(f"  changed: {rel}")
    print(f"  contract_digest: {current.get('contract_digest')} -> {rebuilt['contract_digest']}")

    if args.check:
        drifted = bool(added or changed) or current.get("contract_digest") != rebuilt["contract_digest"]
        print("DRIFT" if drifted else "clean")
        return 1 if drifted else 0

    (ROOT / "manifest.json").write_text(json.dumps(rebuilt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"manifest.json rebuilt: {len(rebuilt['files'])} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
