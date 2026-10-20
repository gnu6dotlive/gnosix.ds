#!/usr/bin/env bash
# Provision the browser the eye looks with.
#
# The eye renders the system's own surfaces and compares the pictures
# with the ones the system carries. The rendering is a fact about the
# browser and the font, so the browser is pinned by the lockfile and the
# font is the one this repository packages: a machine with another
# browser, or another font, produces another picture, and the gate fails
# on a difference that is not a difference.
#
# Prints the environment for the caller to export. Everything
# informational goes to stderr, so the caller can eval the output without
# running the messages as commands:
#
#   eval "$(ci/provision-browser.sh)"
#
# The same script runs in CI, in the release job and in the local
# simulation, so the three cannot drift apart.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EYE="$ROOT/qa/eye"
WORK="${EYE_BROWSER_DIR:-${RUNNER_TEMP:-$ROOT/.ci-cache}}"

if ! command -v node >/dev/null 2>&1; then
  echo "  node is not installed" >&2
  exit 1
fi

mkdir -p "$WORK"

# The packages, from the lockfile. An unlocked install is a variable
# environment, and a picture that depends on a variable environment is
# not reproducible.
if [[ ! -d "$EYE/node_modules" ]]; then
  echo "  installing the pinned packages" >&2
  (cd "$EYE" && npm ci --no-audit --no-fund >/dev/null)
fi

# The browser, in a directory of its own, so the machine's own browsers
# do not decide what the system sees.
export PLAYWRIGHT_BROWSERS_PATH="$WORK/browsers"
if [[ ! -d "$PLAYWRIGHT_BROWSERS_PATH" ]]; then
  echo "  downloading the pinned browser" >&2
  (cd "$EYE" && PLAYWRIGHT_BROWSERS_PATH="$PLAYWRIGHT_BROWSERS_PATH" \
     npx playwright install chromium >/dev/null)
fi

echo "PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH"
