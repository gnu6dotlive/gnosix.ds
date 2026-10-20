#!/usr/bin/env bash
# Provision the FigCraft engine and the packaged font.
#
# The qualification gates rebuild the FigCraft projection and compare it,
# so they need the engine, and the engine lays text out with the fonts it
# finds, and the text layout is part of the file. A machine with a
# different font set produces different bytes and the gate fails on a
# difference that is not a difference.
#
# The engine is pinned by its digest and the font is the one this
# repository packages, installed into a fontconfig directory of its own so
# the result does not depend on what the machine happens to have.
#
# Prints the environment for the caller to export. Everything informational
# goes to stderr, so the caller can eval the output without running the
# messages as commands:
#
#   eval "$(ci/provision-engine.sh)"
#
# The same script runs in CI, in the release job and in the local
# simulation, so the three cannot drift apart.

set -euo pipefail

VERSION="${FIGCRAFT_VERSION:-0.7.0}"
URL="https://github.com/storytold/figcraft/releases/download/v${VERSION}/figcraft-${VERSION}-linux-x86_64.tar.gz"
SHA256="${FIGCRAFT_SHA256:-f3ddf6194d2bbd523cd3195df90fa2cd5782d3946fc7833b7f6bf88fda37908d}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="${FIGCRAFT_ENGINE_DIR:-${RUNNER_TEMP:-$ROOT/.ci-cache}}"

mkdir -p "$WORK"

if [[ ! -x "$WORK/figcraft-engine/bin/figcraft-cli" ]]; then
  echo "  downloading the pinned engine" >&2
  curl -fsSL -o "$WORK/figcraft-engine.tar.gz" "$URL"
  # The check reports on stdout; the caller evals this script's output,
  # so the report goes to stderr with everything else.
  echo "$SHA256  $WORK/figcraft-engine.tar.gz" | sha256sum --check --strict >&2
  mkdir -p "$WORK/figcraft-engine"
  tar xzf "$WORK/figcraft-engine.tar.gz" -C "$WORK/figcraft-engine" --strip-components=1
  chmod +x "$WORK/figcraft-engine/bin/figcraft-cli"
fi

"$WORK/figcraft-engine/bin/figcraft-cli" --version >&2

mkdir -p "$WORK/xdg/fonts" "$WORK/xdg/fontcache"
cp "$ROOT/assets/fonts/SpaceGrotesk-native.ttf" "$WORK/xdg/fonts/"

cat > "$WORK/xdg/fonts.conf" <<FONTCONF
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>$WORK/xdg/fonts</dir>
  <cachedir>$WORK/xdg/fontcache</cachedir>
  <include ignore_missing="yes">/etc/fonts/conf.d</include>
</fontconfig>
FONTCONF

cat <<ENV
export FIGCRAFT_CLI="$WORK/figcraft-engine/bin/figcraft-cli"
export FONTCONFIG_FILE="$WORK/xdg/fonts.conf"
export XDG_DATA_HOME="$WORK/xdg"
ENV
