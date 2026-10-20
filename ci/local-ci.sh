#!/usr/bin/env bash
# local-ci.sh — run the CI job, or the release job, locally, in the
# runner's conditions.
#
# GitHub Actions costs money and credit. This script exists so that a failing
# job is found here, on this machine, at no cost, rather than on the runner.
#
# It reproduces the runner's environment rather than approximating it:
#
#   - a fresh clone, at a different path, so anything that depends on where
#     the repository lives is caught;
#   - the FigCraft engine, downloaded and checked against its digest, with
#     the same version the workflow pins;
#   - the packaged font, in the same fontconfig layout the workflow uses, so
#     the engine finds it the way it finds it there;
#   - the same qualification command the workflow runs.
#
# Then, and only then, push.
#
#   ./ci/local-ci.sh              # the CI job
#   ./ci/local-ci.sh --release    # the release job: qualify, build, and check
#                                 # the archive without publishing anything
#   ./ci/local-ci.sh --no-clone  # against the working tree
#   ./ci/local-ci.sh --keep      # leave the clone in place
#
# The provisioning is the same script the workflows call, so the three
# cannot drift apart.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# The simulation's work lives in the repository, in a directory the
# repository ignores. The clone is a fresh copy of the repository at
# another path, on purpose: that is the runner's condition, and a thing
# that depends on where the repository sits is caught here rather than
# there. The engine and the browser live in the same place, so a machine
# that has them does not fetch them again on every run.
WORK="$REPO/.ci-cache/ci-XXXXXX"
mkdir -p "$REPO/.ci-cache"
WORK="$(mktemp -d "$WORK")"
CLONE=1
KEEP=0
RELEASE=0

for arg in "$@"; do
  case "$arg" in
    --no-clone) CLONE=0 ;;
    --keep) KEEP=1 ;;
    --release) RELEASE=1 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

cleanup() {
  if [[ $KEEP -eq 0 ]]; then rm -rf "$WORK"; else echo "kept: $WORK"; fi
}
trap cleanup EXIT

echo "▸ preparing $WORK"

if [[ $CLONE -eq 1 ]]; then
  git clone -q "$REPO" "$WORK/repo"
  SOURCE="$WORK/repo"
else
  SOURCE="$REPO"
fi

# The engine and the font, from the same script the workflows call.
export RUNNER_TEMP="$REPO/.ci-cache/runner"
mkdir -p "$RUNNER_TEMP"
export FIGCRAFT_ENV_FILE="$REPO/.ci-cache/env"
: > "$FIGCRAFT_ENV_FILE"
"$SOURCE/ci/provision-engine.sh" > /dev/null
"$SOURCE/ci/provision-browser.sh" > /dev/null

cd "$SOURCE"

# The runner has the repository, the pinned toolchains and nothing else.
# This machine has a home directory with other projects in it, and a gate
# that reaches into it finds things the runner will not have: the local
# run passes, the runner fails, and the run on the runner is a failure of
# method rather than of the code. So the qualification runs with the
# machine's data hidden and its toolchains kept — the same conditions,
# the same failure.
ORIGINAL_HOME="$HOME"
EMPTY_HOME="$WORK/home"
mkdir -p "$EMPTY_HOME"
export HOME="$EMPTY_HOME"
export RUSTUP_HOME="${RUSTUP_HOME:-$ORIGINAL_HOME/.rustup}"
export CARGO_HOME="${CARGO_HOME:-$ORIGINAL_HOME/.cargo}"

# The dependencies, at the versions the workflow installs. They are checked
# rather than installed: this machine's Python is externally managed, and
# installing into it is not the simulation's business. A version that is not
# the pinned one is reported, because that is what the runner would have.
python3 - <<'CHECK'
import re, sys
from importlib.metadata import version
wanted = {}
for line in open("requirements.txt"):
    line = line.strip()
    if line and not line.startswith("#") and "==" in line:
        name, pin = line.split("==")
        wanted[name] = pin
bad = []
for name, pin in wanted.items():
    try:
        found = version(name)
    except Exception:
        bad.append(f"{name} is not installed (the workflow installs {pin})")
        continue
    if found != pin:
        bad.append(f"{name} is {found}, the workflow installs {pin}")
if bad:
    for line in bad:
        print("  " + line, file=sys.stderr)
    print("  the local environment does not match the pinned one", file=sys.stderr)
CHECK

# The qualification runs in a fresh shell that reads the environment file
# the provisioning wrote, exactly as a later GitHub Actions step does. A
# single shell would hide a step that forgets to hand the engine on, and
# that is the kind of thing the runner is the wrong place to find out
# about.
echo "▸ running the qualification in $SOURCE (fresh shell)"
(
  set -euo pipefail
  set -a
  # shellcheck disable=SC1090
  . "$FIGCRAFT_ENV_FILE"
  set +a
  python3 -VV
  python3 -m tools.ci
)

if [[ $RELEASE -eq 1 ]]; then
  # Each step runs in a fresh shell that reads the environment file, the
  # way a later GitHub Actions step reads what the earlier one handed on.
  echo "▸ building the distributable archive (fresh shell)"
  (
    set -euo pipefail
    set -a
    # shellcheck disable=SC1090
    . "$FIGCRAFT_ENV_FILE"
    set +a
    python3 -m tools.release build
    echo "▸ checking the release is publishable"
    python3 -m tools.release status
  )
  echo "▸ the release path is proven locally; publish with:"
  echo "    git push origin v$(cat VERSION)"
fi
