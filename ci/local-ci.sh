#!/usr/bin/env bash
# local-ci.sh — run the whole CI job locally, in the runner's conditions.
#
# GitHub Actions cost money and credit. This script exists so that a failing
# job is found here, on this machine, at no cost, rather than on the runner.
#
# It reproduces the runner's environment rather than approximating it:
#
#   - a fresh clone, at a different path, so anything that depends on where
#     the repository lives is caught;
#   - the FigCraft engine, downloaded and checked against its digest, with
#     the same version the workflow pins;
#   - the packaged font, in the same XDG_DATA_HOME layout the workflow
#     uses, so the engine finds it the way it finds it there;
#   - the same qualification command the workflow runs.
#
# Then, and only then, push.
#
#   ./ci/local-ci.sh                 # against the current branch
#   ./ci/local-ci.sh --no-clone      # against the working tree
#   ./ci/local-ci.sh --keep          # leave the clone in place
#
# The setup steps here and in .github/workflows/ci.yml are the same four
# lines of environment. If one changes, the other must change with it, or
# this stops being a faithful reproduction.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/gnosix-ci-XXXXXX")"
CLONE=1
KEEP=0

for arg in "$@"; do
  case "$arg" in
    --no-clone) CLONE=0 ;;
    --keep) KEEP=1 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

# The engine, pinned. Same version and same digest as the workflow.
FIGCRAFT_VERSION="0.7.0"
FIGCRAFT_URL="https://github.com/storytold/figcraft/releases/download/v${FIGCRAFT_VERSION}/figcraft-${FIGCRAFT_VERSION}-linux-x86_64.tar.gz"
FIGCRAFT_SHA256="f3ddf6194d2bbd523cd3195df90fa2cd5782d3946fc7833b7f6bf88fda37908d"

cleanup() {
  if [[ $KEEP -eq 0 ]]; then rm -rf "$WORK"; else echo "kept: $WORK"; fi
}
trap cleanup EXIT

echo "▸ preparing $WORK"

# 1. The engine, outside the checkout, so the manifest gate does not see it.
if [[ ! -x "$WORK/figcraft-engine/bin/figcraft-cli" ]]; then
  if [[ -f "$WORK/figcraft-engine.tar.gz" ]]; then
    :
  else
    echo "  downloading the pinned engine"
    curl -fsSL -o "$WORK/figcraft-engine.tar.gz" "$FIGCRAFT_URL"
  fi
  echo "$FIGCRAFT_SHA256  $WORK/figcraft-engine.tar.gz" | sha256sum --check --strict
  mkdir -p "$WORK/figcraft-engine"
  tar xzf "$WORK/figcraft-engine.tar.gz" -C "$WORK/figcraft-engine" --strip-components=1
  chmod +x "$WORK/figcraft-engine/bin/figcraft-cli"
fi
"$WORK/figcraft-engine/bin/figcraft-cli" --version

# 2. The font, in the layout the engine reads it from.
mkdir -p "$WORK/xdg/fonts"

# 3. A fresh clone, at a different path from the one it came from, so
#    anything that depends on where the repository lives is caught.
if [[ $CLONE -eq 1 ]]; then
  git clone -q "$REPO" "$WORK/repo"
  SOURCE="$WORK/repo"
else
  SOURCE="$REPO"
fi

cp "$SOURCE/assets/fonts/SpaceGrotesk-native.ttf" "$WORK/xdg/fonts/"

export XDG_DATA_HOME="$WORK/xdg"
export FIGCRAFT_CLI="$WORK/figcraft-engine/bin/figcraft-cli"

echo "▸ running the qualification in $SOURCE"
cd "$SOURCE"
python3 -VV
python3 -m tools.ci
