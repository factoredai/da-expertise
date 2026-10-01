"""Validate the top-level catalog: .claude-plugin/marketplace.json.

Covers structure, required fields, field types/formats, and — importantly — that
the catalog and the plugins on disk agree (no orphan or unlisted plugins, and
every ``source`` path resolves).
"""

from __future__ import annotations

import pytest

from helpers import (
    is_email,
    is_nonempty_str,
    is_semver,
    is_str_list,
    require_fields,
)

pytestmark = pytest.mark.marketplace

TOP_LEVEL_FIELDS = ["name", "version", "description", "owner", "metadata", "plugins"]
PLUGIN_ENTRY_FIELDS = ["name", "source", "description", "category", "tags"]


def test_marketplace_exists_and_is_object(marketplace_json):
    assert isinstance(marketplace_json, dict), "marketplace.json must be a JSON object."


def test_marketplace_required_fields(marketplace_json):
    require_fields(marketplace_json, TOP_LEVEL_FIELDS, "marketplace.json")


def test_marketplace_field_types(marketplace_json):
    assert is_nonempty_str(marketplace_json["name"]), "marketplace 'name' must be a non-empty string."
    assert is_semver(marketplace_json["version"]), (
        f"marketplace 'version' must be SemVer X.Y.Z, got {marketplace_json['version']!r}."
    )
    assert is_nonempty_str(marketplace_json["description"]), (
        "marketplace 'description' must be a non-empty string."
    )


def test_marketplace_owner(marketplace_json):
    owner = marketplace_json["owner"]
    require_fields(owner, ["name", "email"], "marketplace.owner")
    assert is_email(owner["email"]), f"marketplace owner email is invalid: {owner['email']!r}."


def test_marketplace_metadata(marketplace_json):
    metadata = marketplace_json["metadata"]
    require_fields(metadata, ["pluginRoot"], "marketplace.metadata")
    assert is_nonempty_str(metadata["pluginRoot"]), "metadata 'pluginRoot' must be a non-empty string."


def test_marketplace_plugins_is_nonempty_list(marketplace_json):
    plugins = marketplace_json["plugins"]
    assert isinstance(plugins, list) and plugins, "'plugins' must be a non-empty list."


def test_plugin_entries_are_valid(marketplace_json):
    for entry in marketplace_json["plugins"]:
        ctx = f"marketplace plugin entry {entry.get('name', '<unknown>')!r}"
        require_fields(entry, PLUGIN_ENTRY_FIELDS, ctx)
        assert is_nonempty_str(entry["name"]), f"{ctx}: 'name' must be a non-empty string."
        assert is_nonempty_str(entry["source"]), f"{ctx}: 'source' must be a non-empty string."
        assert is_nonempty_str(entry["category"]), f"{ctx}: 'category' must be a non-empty string."
        assert is_str_list(entry["tags"]), f"{ctx}: 'tags' must be a non-empty list of strings."


def test_plugin_source_paths_resolve(marketplace_json, repo_root):
    for entry in marketplace_json["plugins"]:
        name, source = entry["name"], entry["source"]
        ctx = f"marketplace plugin entry {name!r}"
        # Convention: source == ./plugins/<name>.
        assert source == f"./plugins/{name}", (
            f"{ctx}: 'source' should be './plugins/{name}', got {source!r}."
        )
        resolved = (repo_root / source).resolve()
        assert resolved.is_dir(), f"{ctx}: 'source' path does not exist on disk: {resolved}."


def test_catalog_and_disk_agree(marketplace_json, plugin_dirs):
    """Every plugin on disk is listed in the catalog, and vice versa."""
    listed = {entry["name"] for entry in marketplace_json["plugins"]}
    on_disk = {p.name for p in plugin_dirs}

    unlisted = on_disk - listed
    assert not unlisted, (
        f"Plugins exist on disk but are not registered in marketplace.json: {sorted(unlisted)}."
    )
    orphaned = listed - on_disk
    assert not orphaned, (
        f"marketplace.json lists plugins with no matching directory under plugins/: "
        f"{sorted(orphaned)}."
    )
