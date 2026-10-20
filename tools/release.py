"""The release lifecycle: bump, build, tag, publish.

The package used to be distributed as a tarball named for its version, built
by hand, with the version written into a dozen files by hand. This module
makes the sequence one thing with one order, so that the tag, the version
file, the manifest and the published archive cannot disagree:

    python -m tools.release status     # where the repository stands
    python -m tools.release bump --minor
    python -m tools.release build      # dist/Gnosix-DS-V<version>.tar.gz
    python -m tools.release tag        # annotated v<version>
    python -m tools.release publish    # GitHub release with the archive

The order is not a convention, it is enforced. `bump` moves the version and
rebuilds the manifest, because the manifest hashes the version file. `tag`
refuses a dirty tree, because a tag names a state and a dirty tree is not
one. `publish` refuses unless the tree is clean, the tag exists, the tag
agrees with the version, and the archive that would be published has already
been built from the same commit.

The archive is built in two layers and the two are reported separately,
because only one of them is a statement about the source alone. The tar
stream inside is byte-reproducible: entries are sorted, timestamps are fixed,
ownership is cleared, and the gzip header carries neither a name nor a time.
The gzip wrapper around it is not, because gzip's output depends on the zlib
build that produced it and two zlib versions do not emit the same compressed
bytes for the same input. The content digest is the one a consumer can check
on their own machine.
"""

import argparse
import gzip
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

# What a consumer receives.
#
# The tools and the tests travel with the package: the validation gates are
# part of the contract, not the machinery that produced it, and a consumer
# is expected to run them before redistributing. V3.4.2 shipped them that way
# and the README tells the reader to run them "from the package root".
#
# The package is the repository minus the CI configuration and the build
# output. Everything else is in it, which is what lets manifest.json
# describe the package exactly: every file the manifest hashes is a file the
# archive carries.
PACKAGED_DIRS = [
    "assets",
    "core",
    "profiles",
    "references",
    "site",
    "qa",
    "tools",
    "tests",
]

PACKAGED_FILES = [
    ".gitattributes",
    ".gitignore",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "THIRD_PARTY_NOTICES.md",
    "VERSION",
    "manifest.json",
    "requirements.txt",
]

# Never packaged.
EXCLUDED = {".git", ".github", "dist", "__pycache__", ".pytest_cache"}

# A fixed timestamp for every archive member. The commit's own time is not
# used, because the archive must be identical whether it is built from a
# fresh clone or from a working tree that has since been touched.
FIXED_MTIME = 0


def run(argv: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, check=False, **kwargs)


def version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def tag_name(version: str) -> str:
    return f"v{version}"


def git(*args: str) -> subprocess.CompletedProcess:
    return run(["git", *args])


def tree_is_dirty() -> list[str]:
    result = git("status", "--porcelain")
    return [line for line in result.stdout.splitlines() if line.strip()]


def current_tag() -> str | None:
    result = git("describe", "--tags", "--exact-match", "HEAD")
    return result.stdout.strip() if result.returncode == 0 else None


def newest_tag() -> str | None:
    result = git("describe", "--tags", "--abbrev=0")
    return result.stdout.strip() if result.returncode == 0 else None


def archive_name(version: str) -> str:
    return f"Gnosix-DS-V{version}.tar.gz"


def archive_root(version: str) -> str:
    return f"Gnosix-DS-V{version}"


# ------------------------------------------------------------------- status

def cmd_status(_args) -> int:
    version_value = version()
    print(f"version         {version_value}")
    print(f"tag for it      {tag_name(version_value)}"
          + ("" if current_tag() else "  (not on this commit)"))
    print(f"newest tag      {newest_tag() or '(none)'}")
    dirty = tree_is_dirty()
    print(f"tree            {'dirty' if dirty else 'clean'}")
    for line in dirty:
        print(f"  {line}")
    print(f"archive         {archive_name(version_value)}")
    return 0


# --------------------------------------------------------------------- bump

def bump(version_value: str, part: str) -> str:
    major, minor, patch = (int(piece) for piece in version_value.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise SystemExit(f"unknown part: {part}")


def cmd_bump(args) -> int:
    current = version()
    target = bump(current, args.part)

    if args.dry_run:
        print(f"{current} -> {target} (dry run, nothing written)")
        return 0

    result = run([sys.executable, "-m", "tools.version", "--set", target])
    if result.returncode != 0:
        print(result.stdout + result.stderr)
        return result.returncode

    # The manifest hashes the version file, so it has to be rebuilt in the
    # same step or the tree is left in a state the contract gate rejects.
    rebuild = run([sys.executable, "-m", "tools.rebuild_manifest"])
    if rebuild.returncode != 0:
        print(rebuild.stdout + rebuild.stderr)
        return rebuild.returncode

    print(f"bumped {current} -> {target}")
    print(f"  VERSION and every slot now carry {target}")
    print(f"  manifest rebuilt")
    print(f"next: commit, then `python -m tools.release tag`")
    return 0


# -------------------------------------------------------------------- build

def packaged_files() -> list[Path]:
    files: list[Path] = []
    for entry in PACKAGED_DIRS:
        path = ROOT / entry
        if not path.is_dir():
            continue
        for child in path.rglob("*"):
            if child.is_file() and not (set(child.parts) & EXCLUDED):
                files.append(child)
    for entry in PACKAGED_FILES:
        path = ROOT / entry
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda p: str(p.relative_to(ROOT)))


def build_archive(version_value: str) -> tuple[Path, str, str]:
    """Build the distributable archive.

    Returns (path, archive digest, content digest).

    Two digests, because the archive has two layers and only one of them is
    a statement about the source alone:

      content  the sha256 of the uncompressed tar stream. Entries are
               sorted, timestamps are fixed, ownership is cleared and modes
               are normalised, so this digest is the same on every machine
               that checks out the same commit.
      archive  the sha256 of the gzip wrapper. The tar inside is
               bit-identical, but gzip's output depends on the zlib build
               that produced it, and two zlib versions do not emit the same
               compressed bytes for the same input.

    Publishing the content digest is what lets a consumer verify that what
    they built is what was published. Verifying the archive digest only
    works on the machine that produced it, which is a weaker statement and
    an easy one to make by accident.
    """
    DIST.mkdir(exist_ok=True)
    target = DIST / archive_name(version_value)
    root = archive_root(version_value)
    files = packaged_files()

    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.GNU_FORMAT) as tar:
        for path in files:
            rel = path.relative_to(ROOT)
            info = tar.gettarinfo(str(path), arcname=f"{root}/{rel}")
            info.mtime = FIXED_MTIME
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mode = 0o644 if not path.stat().st_mode & 0o111 else 0o755
            with path.open("rb") as handle:
                tar.addfile(info, handle)

    content_digest = hashlib.sha256(raw.getvalue()).hexdigest()

    # A gzip header with a name and a timestamp would make the archive
    # depend on when and where it was built. Both are set to nothing.
    packed = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=packed, mtime=0) as gz:
        gz.write(raw.getvalue())
    target.write_bytes(packed.getvalue())

    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    return target, digest, content_digest


def tar_stream_digest(archive: Path) -> str:
    """The sha256 of the uncompressed tar inside an archive."""
    with gzip.open(archive, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def cmd_build(_args) -> int:
    version_value = version()
    target, digest, content_digest = build_archive(version_value)
    size = target.stat().st_size
    print(f"built {target.relative_to(ROOT)}")
    print(f"  {size} bytes")
    print(f"  {len(packaged_files())} files")
    print(f"  sha256 (archive) {digest}")
    print(f"  sha256 (content) {content_digest}")
    print("  the content digest is the machine-independent one: the tar inside")
    print("  the gzip wrapper is bit-identical, but gzip's output depends on")
    print("  the zlib build that produced it")
    return 0


# ---------------------------------------------------------------------- tag

def cmd_tag(args) -> int:
    version_value = version()
    name = tag_name(version_value)

    dirty = tree_is_dirty()
    if dirty and not args.allow_dirty:
        print("the tree is dirty; a tag names a state, and this is not one:")
        for line in dirty:
            print(f"  {line}")
        return 1

    if git("rev-parse", f"refs/tags/{name}").returncode == 0:
        print(f"tag {name} already exists")
        return 1

    message = args.message or f"gnosix_DS {version_value}"
    result = git("tag", "-a", name, "-m", message)
    if result.returncode != 0:
        print(result.stdout + result.stderr)
        return result.returncode
    print(f"tagged {name}")
    return 0


# ------------------------------------------------------------------ publish

def changelog_section(version_value: str) -> str | None:
    path = ROOT / "CHANGELOG.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"^##\s+\[?{re.escape(version_value)}\]?.*?(?=^##\s|\Z)", re.M | re.S)
    match = pattern.search(text)
    return match.group(0).strip() if match else None


def cmd_publish(args) -> int:
    version_value = version()
    name = tag_name(version_value)

    dirty = tree_is_dirty()
    if dirty:
        print("the tree is dirty; refusing to publish an uncommitted state:")
        for line in dirty:
            print(f"  {line}")
        return 1

    if current_tag() != name:
        print(f"HEAD is not tagged {name}"
              + (f" (it is {current_tag()})" if current_tag() else " (it is untagged)"))
        return 1

    target = DIST / archive_name(version_value)
    if not target.exists():
        print(f"{target.relative_to(ROOT)} does not exist; run `python -m tools.release build`")
        return 1

    notes = changelog_section(version_value)
    if notes is None and not args.allow_missing_notes:
        print(f"CHANGELOG.md has no section for {version_value}")
        return 1

    # The content digest goes in the notes because it is the one a consumer
    # can check: they rebuild the archive and compare the tar inside it, and
    # it matches whatever machine built the published one.
    notes = (notes or "") + (
        f"\n\n---\n\nContent digest (sha256 of the uncompressed tar): "
        f"`{tar_stream_digest(target)}`\n"
    )

    argv = ["gh", "release", "create", name, str(target.relative_to(ROOT))]
    if notes:
        argv += ["--notes", notes]
    if args.draft:
        argv.append("--draft")
    if args.title:
        argv += ["--title", args.title]
    else:
        argv += ["--title", f"gnosix_DS {version_value}"]

    result = run(argv)
    if result.returncode != 0:
        print(result.stdout + result.stderr)
        return result.returncode
    print(result.stdout.strip())
    print(f"published {name} with {target.relative_to(ROOT)}")
    return 0


# --------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="the release lifecycle")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="where the repository stands").set_defaults(func=cmd_status)

    bump_parser = sub.add_parser("bump", help="move the version and rebuild the manifest")
    bump_group = bump_parser.add_mutually_exclusive_group(required=True)
    bump_group.add_argument("--patch", dest="part", action="store_const", const="patch",
                            help="raise the patch number")
    bump_group.add_argument("--minor", dest="part", action="store_const", const="minor",
                            help="raise the minor number")
    bump_group.add_argument("--major", dest="part", action="store_const", const="major",
                            help="raise the major number")
    bump_parser.add_argument("--dry-run", action="store_true")
    bump_parser.set_defaults(func=cmd_bump)

    sub.add_parser("build", help="build the distributable archive").set_defaults(func=cmd_build)

    tag_parser = sub.add_parser("tag", help="create the annotated release tag")
    tag_parser.add_argument("--message")
    tag_parser.add_argument("--allow-dirty", action="store_true")
    tag_parser.set_defaults(func=cmd_tag)

    publish_parser = sub.add_parser("publish", help="publish the GitHub release")
    publish_parser.add_argument("--draft", action="store_true")
    publish_parser.add_argument("--title")
    publish_parser.add_argument("--allow-missing-notes", action="store_true")
    publish_parser.set_defaults(func=cmd_publish)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
