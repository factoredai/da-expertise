"""Validate each plugin manifest: plugins/<id>/.claude-plugin/plugin.json.

Parametrized per plugin (see conftest.pytest_generate_tests) so each plugin is a
distinct test case in `pytest -v` output.
"""

from __future__ import annotations

import pytest

from helpers import (
    is_email,
    is_nonempty_str,
    is_semver,
    is_str_list,
    load_json,
    require_fields,
)

pytestmark = pytest.mark.plugin

PLUGIN_FIELDS = ["name", "displayName", "version", "description", "author", "keywords"]


def _manifest(plugin_dir):
    return load_json(plugin_dir / ".claude-plugin" / "plugin.json")


def test_plugin_manifest_exists_and_is_object(plugin_dir):
    manifest = _manifest(plugin_dir)
    assert isinstance(manifest, dict), f"{plugin_dir.name}: plugin.json must be a JSON object."


def test_plugin_required_fields(plugin_dir):
    manifest = _manifest(plugin_dir)
    require_fields(manifest, PLUGIN_FIELDS, f"{plugin_dir.name}/plugin.json")


def test_plugin_field_types(plugin_dir):
    manifest = _manifest(plugin_dir)
    ctx = f"{plugin_dir.name}/plugin.json"
    assert is_nonempty_str(manifest["displayName"]), f"{ctx}: 'displayName' must be a non-empty string."
    assert is_nonempty_str(manifest["description"]), f"{ctx}: 'description' must be a non-empty string."
    assert is_semver(manifest["version"]), (
        f"{ctx}: 'version' must be SemVer X.Y.Z, got {manifest['version']!r}."
    )
    assert is_str_list(manifest["keywords"]), f"{ctx}: 'keywords' must be a non-empty list of strings."
    # 'category'/'tags' are optional overrides consumed by utils/marketplace_sync.py;
    # when present they must be well-formed, but omitting them is valid.
    if "category" in manifest:
        assert is_nonempty_str(manifest["category"]), f"{ctx}: 'category' must be a non-empty string."
    if "tags" in manifest:
        assert is_str_list(manifest["tags"]), f"{ctx}: 'tags' must be a non-empty list of strings."


def test_plugin_author(plugin_dir):
    manifest = _manifest(plugin_dir)
    author = manifest["author"]
    require_fields(author, ["name", "email"], f"{plugin_dir.name}/plugin.json author")
    assert is_email(author["email"]), (
        f"{plugin_dir.name}/plugin.json: author email is invalid: {author['email']!r}."
    )


def test_plugin_name_matches_directory(plugin_dir):
    manifest = _manifest(plugin_dir)
    assert manifest["name"] == plugin_dir.name, (
        f"plugin.json 'name' ({manifest['name']!r}) must match the plugin directory "
        f"name ({plugin_dir.name!r})."
    )


def test_plugin_name_matches_marketplace(plugin_dir, marketplace_json):
    manifest = _manifest(plugin_dir)
    listed = {entry["name"] for entry in marketplace_json["plugins"]}
    assert manifest["name"] in listed, (
        f"plugin {manifest['name']!r} is not registered in marketplace.json 'plugins'."
    )


def test_plugin_has_skills(plugin_dir):
    skills_root = plugin_dir / "skills"
    assert skills_root.is_dir(), f"{plugin_dir.name}: missing 'skills/' directory."
    skills = [s for s in skills_root.iterdir() if s.is_dir() and (s / "SKILL.md").is_file()]
    assert skills, f"{plugin_dir.name}: 'skills/' must contain at least one skill with a SKILL.md."
