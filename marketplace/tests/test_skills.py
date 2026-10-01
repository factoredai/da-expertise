"""Validate each skill: plugins/<id>/skills/<name>/SKILL.md.

Parametrized per skill (see conftest.pytest_generate_tests) so each skill is a
distinct test case in `pytest -v` output.
"""

from __future__ import annotations

import pytest

from helpers import is_kebab_case, is_nonempty_str, parse_frontmatter, require_fields

pytestmark = pytest.mark.skill

REQUIRED_FRONTMATTER_FIELDS = ["name", "description"]
# The convention today is exactly {name, description}. Keep this list as the single
# place to extend if new optional keys become official (e.g. "version", "tags").
ALLOWED_FRONTMATTER_FIELDS = {"name", "description"}


def test_skill_md_exists(skill_dir):
    assert (skill_dir / "SKILL.md").is_file(), f"{skill_dir.name}: missing SKILL.md."


def test_skill_frontmatter_parses(skill_dir):
    # parse_frontmatter raises a readable AssertionError on any structural problem.
    fm = parse_frontmatter(skill_dir / "SKILL.md")
    assert isinstance(fm, dict), f"{skill_dir.name}: frontmatter must be a YAML mapping."


def test_skill_required_fields(skill_dir):
    fm = parse_frontmatter(skill_dir / "SKILL.md")
    require_fields(fm, REQUIRED_FRONTMATTER_FIELDS, f"{skill_dir.name}/SKILL.md frontmatter")


def test_skill_name_is_kebab_case(skill_dir):
    fm = parse_frontmatter(skill_dir / "SKILL.md")
    assert is_kebab_case(fm["name"]), (
        f"{skill_dir.name}/SKILL.md: 'name' must be lowercase kebab-case, got {fm['name']!r}."
    )


def test_skill_name_matches_directory(skill_dir):
    fm = parse_frontmatter(skill_dir / "SKILL.md")
    assert fm["name"] == skill_dir.name, (
        f"SKILL.md 'name' ({fm['name']!r}) must match the skill directory name "
        f"({skill_dir.name!r})."
    )


def test_skill_description_nonempty(skill_dir):
    fm = parse_frontmatter(skill_dir / "SKILL.md")
    assert is_nonempty_str(fm["description"]), (
        f"{skill_dir.name}/SKILL.md: 'description' must be a non-empty string."
    )


def test_skill_no_unexpected_frontmatter_keys(skill_dir):
    fm = parse_frontmatter(skill_dir / "SKILL.md")
    unexpected = set(fm) - ALLOWED_FRONTMATTER_FIELDS
    assert not unexpected, (
        f"{skill_dir.name}/SKILL.md: unexpected frontmatter key(s) {sorted(unexpected)}. "
        f"Allowed keys: {sorted(ALLOWED_FRONTMATTER_FIELDS)}. "
        f"If this is a new official field, add it to ALLOWED_FRONTMATTER_FIELDS in tests/test_skills.py."
    )
