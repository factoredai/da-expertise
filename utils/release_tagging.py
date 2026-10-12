"""Compute and create ``<plugin-id>@v<semver>`` release tags (README.md step 5).

For each plugin on disk, compares its ``plugin.json`` version against the
latest existing git tag matching ``<plugin-id>@v*``. A plugin is "pending" if
it has no such tag yet, or if its manifest version is strictly newer than the
latest tagged one. Tag/push are separate, opt-in steps since they're
hard-to-undo operations on shared history.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(REPO_ROOT / "tests"))
from helpers import is_semver, load_json  # noqa: E402

from marketplace_sync import discover_plugin_dirs  # noqa: E402

TAG_VERSION_RE = re.compile(r"^(?P<plugin>.+)@v(?P<version>\d+\.\d+\.\d+)$")


def _version_tuple(version: str) -> tuple[int, int, int]:
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def existing_tag_versions(name: str, repo_root: Path) -> list[tuple[int, int, int]]:
    """Every existing '<name>@vX.Y.Z' tag's version, as a sortable tuple."""
    result = subprocess.run(
        ["git", "tag", "-l", f"{name}@v*"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    versions = []
    for line in result.stdout.splitlines():
        match = TAG_VERSION_RE.match(line.strip())
        if match and match.group("plugin") == name:
            versions.append(_version_tuple(match.group("version")))
    return versions


def pending_tags(repo_root: Path) -> list[tuple[str, str]]:
    """[(plugin_name, version), ...] for plugins that need a new release tag."""
    pending: list[tuple[str, str]] = []
    for plugin_dir in discover_plugin_dirs(repo_root):
        manifest = load_json(plugin_dir / ".claude-plugin" / "plugin.json")
        name, version = manifest["name"], manifest["version"]
        if not is_semver(version):
            continue

        tagged = existing_tag_versions(name, repo_root)
        if not tagged or _version_tuple(version) > max(tagged):
            pending.append((name, version))
    return pending


def create_tag(name: str, version: str, *, push: bool = False, repo_root: Path) -> None:
    """Create the '<name>@v<version>' git tag, optionally pushing it."""
    tag = f"{name}@v{version}"
    subprocess.run(["git", "tag", tag], cwd=repo_root, check=True)
    if push:
        subprocess.run(["git", "push", "origin", tag], cwd=repo_root, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--apply", action="store_true", help="Create the pending tags locally (default: dry-run)."
    )
    parser.add_argument(
        "--push", action="store_true", help="Also push created tags to origin. Requires --apply."
    )
    args = parser.parse_args(argv)

    if args.push and not args.apply:
        parser.error("--push requires --apply")

    pending = pending_tags(args.repo_root)
    if not pending:
        print("No pending release tags.")
        return 0

    for name, version in pending:
        if args.apply:
            create_tag(name, version, push=args.push, repo_root=args.repo_root)
            print(f"Tagged {name}@v{version}" + (" and pushed." if args.push else "."))
        else:
            print(f"Would tag {name}@v{version} (dry-run; pass --apply to create it).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
