#!/usr/bin/env python3
"""Qualify the native profile.

The native projection is published, and its values are the contract's own
constants rather than a second transcription of them. That is worth
nothing if nothing checks it, and a projection that compiles is not the
same thing as a projection that carries the right numbers.

This builds the crate and runs its tests. The crate has no dependencies,
so the build is fast and needs no network.

The gate is a skip, not a pass, when the machine has no Rust toolchain:
a runner without cargo cannot prove the native profile, and saying so is
honest. Exit code 3 is the repository's third answer - it could not run.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRATE = ROOT / "profiles/native"
SKIP = 3


def main() -> int:
    cargo = shutil.which("cargo")
    if cargo is None:
        print("no cargo on this machine; the native profile could not be qualified")
        return SKIP

    # The build output goes outside the package. A build artefact that
    # lands inside the tree is a file the manifest has to hash, and a
    # manifest that depends on whether the crate happened to be built is
    # a manifest that fails on a clean machine.
    environment = dict(os.environ)
    environment["CARGO_TARGET_DIR"] = tempfile.mkdtemp(prefix="gnosix-native-")

    result = subprocess.run(
        [cargo, "test", "--offline", "--quiet"],
        cwd=CRATE, capture_output=True, text=True, check=False, env=environment)
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        print(output)
        return result.returncode

    # The tests must have run, not merely compiled. "test result: ok" with
    # nothing behind it is a crate with no tests in it, which is not a
    # qualified projection.
    passed = sum(int(n) for n in re.findall(r"test result: ok\. (\d+) passed", output))
    if passed == 0:
        print(output)
        print("the native crate ran no tests")
        return 1
    print(output)
    print(f"{passed} native test(s) passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
