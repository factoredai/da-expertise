"""Full-scan ``plugins/`` and reconcile it into ``.claude-plugin/marketplace.json``.

Intended to be invoked by CI (see README.md's "Submit Pull Request" step) as
well as run locally. Every plugin directory containing a valid
``.claude-plugin/plugin.json`` becomes (or updates) an entry in the catalog's
``plugins[]`` list; catalog entries with no matching directory on disk are
dropped. Re-running with no changes on disk is a no-op (idempotent), so CI can
run this on every PR without generating noisy diffs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

# Reuse the marketplace suite's validators instead of redefining them here.
sys.path.insert(0, str(REPO_ROOT / "tests"))
from helpers import is_nonempty_str, is_str_list, load_json  # noqa: E402

DEFAULT_CATEGORY = "Uncategorized"


def discover_plugin_dirs(repo_root: Path) -> list[Path]:
    """Every immediate subdirectory of plugins/ that holds a plugin manifest."""
    plugins_root = repo_root / "plugins"
    if not plugins_root.is_dir():
        return []
    return sorted(
        p
        for p in plugins_root.iterdir()
        if p.is_dir() and (p / ".claude-plugin" / "plugin.json").is_file()
    )


def build_entry(manifest: dict[str, Any]) -> dict[str, Any]:
    """Construct a marketplace ``plugins[]`` entry from a plugin.json manifest.

    ``category``/``tags`` are optional on plugin.json; when absent, fall back
    to a generic category and to ``keywords`` respectively, so a plugin is
    still cataloged even before an expertise group curates real ones.
    """
    name = manifest["name"]
    category = manifest.get("category")
    if not is_nonempty_str(category):
        category = DEFAULT_CATEGORY

    tags = manifest.get("tags")
    if not is_str_list(tags):
        tags = manifest.get("keywords", [])

    return {
        "name": name,
        "source": f"./plugins/{name}",
        "description": manifest["description"],
        "category": category,
        "tags": tags,
    }


def sync_marketplace(repo_root: Path, *, write: bool = True) -> tuple[dict[str, Any], bool]:
    """Reconcile marketplace.json against the plugins found on disk.

    Returns ``(marketplace_dict, changed)``. When ``write`` is True and the
    result differs from what's currently on disk, the file is rewritten.
    """
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"
    marketplace = load_json(marketplace_path)
    existing_by_name = {entry["name"]: entry for entry in marketplace["plugins"]}

    on_disk = discover_plugin_dirs(repo_root)
    on_disk_names = set()
    new_plugins: list[dict[str, Any]] = []

    for plugin_dir in on_disk:
        manifest = load_json(plugin_dir / ".claude-plugin" / "plugin.json")
        name = manifest["name"]
        on_disk_names.add(name)

        built = build_entry(manifest)
        current = existing_by_name.get(name)
        if current is not None:
            # Preserve hand-curated category/tags unless plugin.json now
            # explicitly sets its own — refresh only description/source.
            merged = dict(current)
            merged["source"] = built["source"]
            merged["description"] = built["description"]
            if is_nonempty_str(manifest.get("category")):
                merged["category"] = built["category"]
            if is_str_list(manifest.get("tags")):
                merged["tags"] = built["tags"]
            new_plugins.append(merged)
        else:
            new_plugins.append(built)

    # Drop catalog entries whose plugin directory no longer exists on disk.
    new_plugins.sort(key=lambda entry: entry["name"])

    updated = dict(marketplace)
    updated["plugins"] = new_plugins

    changed = updated != marketplace
    if write and changed:
        marketplace_path.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")

    return updated, changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root to scan (defaults to the repo containing this script).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only report whether the catalog is out of sync; exit 1 if so, without writing.",
    )
    args = parser.parse_args(argv)

    _, changed = sync_marketplace(args.repo_root, write=not args.check)

    if args.check:
        if changed:
            print("marketplace.json is out of sync with plugins/ on disk.")
            return 1
        print("marketplace.json is in sync with plugins/ on disk.")
        return 0

    print("marketplace.json updated." if changed else "marketplace.json already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
