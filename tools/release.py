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
# The package is the repository minus the CI configuration, the local
# simulation of it, the FigCraft projection and the build output.
# Everything else is in it, which is what lets manifest.json describe the
# package exactly: every file the manifest hashes is a file the archive
# carries.
#
# "figcraft" is excluded because it is a 6 MB design-editor document for one
# target among several, and the package ships the portable contract and the
# small projections of it. A consumer who wants the FigCraft projection
# clones the repository; it is not redistributed to everyone who takes the
# tarball.
#
# "ci" is excluded for the same reason and one more: it exists to keep
# GitHub Actions from being used as a test bench, and a script that runs a
# local simulation of the CI has no business in a distributed package.
#
# "handoff" is the web code generated from the projection: the repository's
# own surface, not part of the contract it ships.
#
# "packaging" is the gnu6-design package, and it is in the package on
# purpose: it is the artefact a consumer vendors, cut from the contract
# by a tool that ships with the contract. A package whose whole purpose
# is to be distributed is not distributed otherwise.
PACKAGED_DIRS = [
    "assets",
    "packaging",
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

PROOF = ROOT / ".release-proof.json"


def head_commit() -> str:
    result = git("rev-parse", "HEAD")
    return result.stdout.strip()


def cmd_prove(args) -> int:
    """Run the release job locally and record the proof.

    A GitHub Actions run costs money and credit. The release job qualifies
    the tagged state, builds the archive and publishes it, and every one of
    those three can be done here first. This runs the first two and
    records what it found, so that `tag` and the push hook can refuse to
    publish a state that was never proved.
    """
    script = ROOT / "ci" / "local-ci.sh"
    if not script.is_file():
        print("no ci/local-ci.sh to run", file=sys.stderr)
        return 1
    result = subprocess.run([str(script), "--release"], cwd=ROOT, check=False)
    if result.returncode != 0:
        return result.returncode

    # The guard belongs with the proof: a proof nobody is stopped from
    # ignoring is a note in a file.
    hook = ROOT / "ci" / "pre-push.sh"
    installed = ROOT / ".git" / "hooks" / "pre-push"
    if hook.is_file():
        installed.parent.mkdir(parents=True, exist_ok=True)
        # The guard is a wrapper, not a copy. A copy goes stale the moment
        # the repository's own guard changes, and a guard that has gone
        # stale is a guard that is not there: the installed copy was from
        # the day before the guard learned to qualify a branch, and it had
        # been pushing unqualified commits ever since. The installed hook
        # runs the repository's own file, so the two cannot differ.
        wrapper = ("#!/usr/bin/env bash\n"
                   "# Installed by tools.release prove. It runs the repository's\n"
                   "# own guard, so the guard cannot go stale.\n"
                   'exec "$(git rev-parse --show-toplevel)/ci/pre-push.sh" "$@"\n')
        if not installed.exists() or installed.read_text(encoding="utf-8") != wrapper:
            installed.write_text(wrapper, encoding="utf-8")
            installed.chmod(0o755)
            print(f"installed the push guard at {installed}")

    version_value = version()
    _, archive_digest, content_digest = build_archive(version_value)
    proof = {
        "version": version_value,
        "commit": head_commit(),
        "archive_digest": archive_digest,
        "content_digest": content_digest,
    }
    PROOF.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print(f"proof recorded for {version_value} at {proof['commit'][:12]}")
    return 0


def check_proof() -> str | None:
    """Why the state may not be published, or None when it may."""
    if not PROOF.is_file():
        return ("no local proof; run `python3 -m tools.release prove` "
                "before tagging or pushing a tag")
    try:
        proof = json.loads(PROOF.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "the local proof is unreadable; run `python3 -m tools.release prove`"
    if proof.get("version") != version():
        return (f"the proof is for {proof.get('version')}, the version is {version()}")
    if proof.get("commit") != head_commit():
        return ("the proof is for another commit; run `python3 -m tools.release prove` again")
    try:
        _, _, content_digest = build_archive(version())
    except OSError as exc:
        return f"the archive could not be built: {exc}"
    if proof.get("content_digest") != content_digest:
        return "the archive does not match the proof; run `python3 -m tools.release prove` again"
    return None


def cmd_tag(args) -> int:
    version_value = version()
    name = tag_name(version_value)

    if not args.skip_proof:
        problem = check_proof()
        if problem:
            print(f"the release job has not been proved locally: {problem}")
            return 1

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


def existing_release(name: str) -> dict | None:
    """The release that already carries this tag, if any.

    The release may already exist: the tag is pushed, the workflow
    publishes it, and a person may also have published it by hand
    before the workflow reached that step. A collision is not a reason to
    fail a release that is already correct.
    """
    result = run(["gh", "release", "view", name, "--json", "body,assets,tagName,isDraft"])
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError):
        return None


def published_digest(notes: str | None) -> str | None:
    """The content digest a published release claims, read from its notes.

    The digest is the one a consumer can check on their own machine: the
    sha256 of the uncompressed tar, which does not depend on the zlib
    build that produced the gzip wrapper.
    """
    match = re.search(r"Content digest \(sha256 of the uncompressed tar\):\s*`([0-9a-f]{64})`",
                      notes or "")
    return match.group(1) if match else None


def cmd_publish(args) -> int:
    version_value = version()
    name = tag_name(version_value)

    # The proof is what a *person* is stopped from publishing an unproved
    # state. The release workflow is the proved job itself, running on the
    # runner, and it has no local proof to present.
    if not args.skip_proof:
        problem = check_proof()
        if problem:
            print(f"the release job has not been proved locally: {problem}")
            return 1

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

    # A release that already exists is not a failure when it is already
    # the one this tree would publish. The tag is pushed, the workflow
    # publishes it, and a person may have published it by hand first; the
    # two must not argue over the same release. The content digest decides
    # it, because that is the one number that is a statement about the
    # source rather than about the machine that compressed it.
    existing = existing_release(name)
    if existing is not None:
        local_digest = tar_stream_digest(target)
        remote_digest = published_digest(existing.get("body"))
        if remote_digest == local_digest:
            print(f"{name} is already published with the same content digest")
            print(f"  {local_digest}")
            print("nothing to do: the published release is the one this tree would publish")
            return 0
        print(f"{name} already exists, with a different content digest")
        print(f"  published: {remote_digest or 'none'}")
        print(f"  this tree: {local_digest}")
        return 1

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

    sub.add_parser("prove", help="run the release job locally and record the proof") \
        .set_defaults(func=cmd_prove)

    def _cmd_check_proof(args) -> int:
        problem = check_proof()
        if problem:
            print(problem, file=sys.stderr)
            return 1
        return 0

    sub.add_parser("check-proof", help="exit non-zero when the state is not proved") \
        .set_defaults(func=_cmd_check_proof)

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
    tag_parser.add_argument("--skip-proof", action="store_true",
                             help="tag without a local proof (not advised)")
    tag_parser.set_defaults(func=cmd_tag)

    publish_parser = sub.add_parser("publish", help="publish the GitHub release")
    publish_parser.add_argument("--draft", action="store_true")
    publish_parser.add_argument("--title")
    publish_parser.add_argument("--allow-missing-notes", action="store_true")
    publish_parser.add_argument("--skip-proof", action="store_true",
                                help="publish without a local proof (the release workflow)")
    publish_parser.set_defaults(func=cmd_publish)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
