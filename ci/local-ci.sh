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
WORK="$(mktemp -d "${TMPDIR:-/tmp}/gnosix-ci-XXXXXX")"
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
export RUNNER_TEMP="$WORK/runner"
mkdir -p "$RUNNER_TEMP"
eval "$("$SOURCE/ci/provision-engine.sh")"

cd "$SOURCE"
python3 -VV

echo "▸ running the qualification in $SOURCE"
python3 -m tools.ci

if [[ $RELEASE -eq 1 ]]; then
  echo "▸ building the distributable archive"
  python3 -m tools.release build
  echo "▸ checking the release is publishable"
  python3 -m tools.release status
  echo "▸ the release path is proven locally; publish with:"
  echo "    git push origin v$(cat VERSION)"
fi
