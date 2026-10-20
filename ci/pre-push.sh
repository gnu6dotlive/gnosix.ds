#!/usr/bin/env bash
# pre-push — refuse to push a tag that was never proved locally.
#
# A GitHub Actions run costs money and credit, and a release job that fails
# on the runner is a release job that should have been run here first.
# This hook makes that structural rather than a matter of remembering: a tag
# can only be pushed if the local release proof matches the commit, the
# version and the archive that would be published.
#
# Branches are not checked. Pushing a branch triggers the CI job, and the
# CI job is what the local simulation covers; a tag triggers the release
# job, which publishes, and that is the one that costs.

set -euo pipefail

REPO="$(git rev-parse --show-toplevel)"
ZERO="0000000000000000000000000000000000000000"

# The refs being pushed, and what they point at, from the hook's arguments.
while read -r local_ref local_sha remote_ref remote_sha; do
  case "$remote_ref" in
    refs/tags/*) ;;
    *) continue ;;
  esac

  if [[ "$local_sha" == "$ZERO" ]]; then
    echo "pre-push: deleting a tag does not need a proof." >&2
    continue
  fi

  cd "$REPO"
  problem="$(python3 -m tools.release check-proof 2>&1)" && continue

  echo "pre-push: refusing to push $remote_ref." >&2
  echo "pre-push: $problem" >&2
  echo "pre-push: run 'python3 -m tools.release prove' and try again." >&2
  exit 1
done

exit 0
