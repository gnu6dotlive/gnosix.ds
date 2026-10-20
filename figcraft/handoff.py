#!/usr/bin/env python3
"""Generate the web code for a board of the FigCraft projection.

The projection is the design source; this turns a board of it into the code
a web project would actually ship: markup, a React component and the
stylesheet. It is the Dev Mode of the engine, driven from a script, so the
result is a build artefact rather than something a person copies by hand.

    python3 figcraft/handoff.py --board "Web / Landing"
    python3 figcraft/handoff.py --board "Web / Landing" --out handoff/

Writes, per board: <name>.html, <name>.tsx and <name>.css.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def query(cli: str, project: Path, steps: list[dict]) -> list:
    """Run commands against the project and return their results."""
    script = "\n".join(json.dumps(step) for step in steps) + "\n"
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as handle:
        handle.write(script)
        path = Path(handle.name)
    try:
        result = subprocess.run([cli, "run", str(path), "--in", str(project)],
                                cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    finally:
        path.unlink(missing_ok=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit("the engine refused the query")

    out = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        step = json.loads(line)
        if not step.get("ok"):
            raise SystemExit(f"the engine refused a query: {step.get('error')}")
        out.append(step.get("result"))
    return out


def find_layer(node: dict, name: str) -> dict | None:
    """A layer by its name, anywhere in the tree."""
    if node.get("name") == name:
        return node
    for child in node.get("children", []) or []:
        found = find_layer(child, name)
        if found:
            return found
    return None


def slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return re.sub(r"-{2,}", "-", s) or "board"


def generate(cli: str, project: Path, board_name: str, out: Path) -> list[str]:
    """Write the web code for a board. Returns the file names."""
    doc = query(cli, project, [{"command": "page.list", "params": {}}])[0]
    board = None
    for page in doc or []:
        tree = query(cli, project,
                     [{"command": "node.get", "params": {"id": page["id"], "depth": 3}}])[0]
        board = find_layer(tree or {}, board_name)
        if board:
            break
    if not board:
        raise SystemExit(f"no board named {board_name!r} in {project}")

    results = query(cli, project, [
        {"command": "inspect.code", "params": {"id": board["id"], "language": "html"}},
        {"command": "inspect.code", "params": {"id": board["id"], "language": "react"}},
    ])
    html = (results[0] or {}).get("code", "")
    react = (results[1] or {}).get("code", "")

    # The React output ends with the stylesheet in a comment; split it out so
    # the stylesheet is a file of its own rather than a string at the end of
    # another one.
    css = ""
    if "/* " in react and ".css */" in react:
        head, css = react.split("/* ", 1)
        css = css.split(" */", 1)[1]
        react = head.rstrip()
    else:
        match = re.search(r"<style>(.*)</style>", html, re.S)
        if match:
            css = match.group(1)
            html = re.sub(r"<style>.*?</style>", "", html, flags=re.S)

    base = slug(board.get("name", "board"))
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for name, content in ((f"{base}.html", html), (f"{base}.tsx", react),
                          (f"{base}.css", css.strip() + "\n")):
        if not content.strip():
            continue
        (out / name).write_text(content, encoding="utf-8")
        written.append(name)
    return written


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="generate the web code for a board")
    parser.add_argument("--project", default=str(REPO_ROOT / "figcraft" / "gnosix-ds.figcraft"))
    parser.add_argument("--board", required=True, help="the board's name")
    parser.add_argument("--out", default=str(REPO_ROOT / "handoff"))
    parser.add_argument("--cli", default=os.environ.get("FIGCRAFT_CLI",
                                                        os.path.expanduser("~/.local/bin/figcraft-cli")))
    parser.add_argument("--check", action="store_true",
                        help="regenerate and compare with the committed files; write nothing")
    args = parser.parse_args(argv)

    project = Path(args.project)
    if not project.is_file():
        raise SystemExit(f"no projection at {project}")
    out = Path(args.out)

    if args.check:
        if not out.is_dir() or not any(out.iterdir()):
            print(f"FAIL: {out} is empty; run the handoff to fill it")
            return 1
        with tempfile.TemporaryDirectory() as tmp:
            written = generate(args.cli, project, args.board, Path(tmp))
            problems = []
            for name in written:
                committed = out / name
                fresh = Path(tmp) / name
                if not committed.is_file():
                    problems.append(f"{name}: missing from {out}")
                elif committed.read_text(encoding="utf-8") != fresh.read_text(encoding="utf-8"):
                    problems.append(f"{name}: the committed file differs from the design")
            if problems:
                print(f"FAIL: {len(problems)} file(s) have drifted from the design")
                for problem in problems:
                    print(f"  - {problem}")
                print("  run the handoff to bring it back")
                return 1
        print(f"PASS: the web code matches the design ({len(written)} files)")
        return 0

    written = generate(args.cli, project, args.board, out)
    print(f"{args.board}: {', '.join(written)} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
