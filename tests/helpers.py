"""Reusable, dependency-light validators for the marketplace test suite.

These are plain Python functions (no jsonschema) so contributors can read and
extend them easily. Every helper aims to fail with a message that names the
offending file/field and the context, so a failing PR check is self-explanatory.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

# X.Y.Z semantic version (the subset the marketplace uses). Pre-release/build
# suffixes are intentionally not accepted to keep versions simple and sortable.
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Loose email check — enough to catch obvious mistakes (missing @ or domain)
# without rejecting valid addresses.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Skill and plugin identifiers use kebab-case (lowercase words joined by hyphens).
KEBAB_CASE_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def load_json(path: Path) -> Any:
    """Parse a JSON file, raising a readable error on missing file / bad syntax."""
    if not path.exists():
        raise AssertionError(f"Expected JSON file does not exist: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Invalid JSON in {path}: {exc}") from exc


def parse_frontmatter(skill_md_path: Path) -> dict:
    """Return the parsed YAML frontmatter mapping from a SKILL.md file.

    Frontmatter is the block delimited by a leading ``---`` line and the next
    ``---`` line. Handles YAML folded (``>``) descriptions via ``yaml.safe_load``.
    Raises a readable AssertionError if the file or frontmatter is missing/invalid.
    """
    if not skill_md_path.exists():
        raise AssertionError(f"SKILL.md does not exist: {skill_md_path}")

    text = skill_md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not lines or lines[0].strip() != "---":
        raise AssertionError(
            f"{skill_md_path} must start with a YAML frontmatter block "
            f"delimited by '---' on the first line."
        )

    # Find the closing '---' delimiter.
    closing_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            closing_idx = idx
            break
    if closing_idx is None:
        raise AssertionError(
            f"{skill_md_path} has an unterminated frontmatter block "
            f"(missing closing '---')."
        )

    block = "\n".join(lines[1:closing_idx])
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        raise AssertionError(f"Invalid YAML frontmatter in {skill_md_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise AssertionError(
            f"Frontmatter in {skill_md_path} must be a YAML mapping, "
            f"got {type(data).__name__}."
        )
    return data


def is_nonempty_str(value: Any) -> bool:
    """True if value is a string with non-whitespace content."""
    return isinstance(value, str) and bool(value.strip())


def is_str_list(value: Any, *, allow_empty: bool = False) -> bool:
    """True if value is a list of non-empty strings."""
    if not isinstance(value, list):
        return False
    if not value and not allow_empty:
        return False
    return all(is_nonempty_str(item) for item in value)


def is_semver(value: Any) -> bool:
    """True if value is an X.Y.Z semantic version string."""
    return isinstance(value, str) and bool(SEMVER_RE.match(value))


def is_email(value: Any) -> bool:
    """True if value looks like a valid email address."""
    return isinstance(value, str) and bool(EMAIL_RE.match(value))


def is_kebab_case(value: Any) -> bool:
    """True if value is a lowercase kebab-case identifier."""
    return isinstance(value, str) and bool(KEBAB_CASE_RE.match(value))


def require_fields(obj: Any, fields: list[str], ctx: str) -> None:
    """Assert that ``obj`` is a mapping containing each field as a non-empty value.

    ``ctx`` describes what is being validated (e.g. a file path or entry name) and
    is included in every failure message so errors point straight to the fix.
    """
    assert isinstance(obj, dict), f"{ctx}: expected a JSON/YAML object, got {type(obj).__name__}."
    for field in fields:
        assert field in obj, f"{ctx}: missing required field '{field}'."
        value = obj[field]
        if isinstance(value, str):
            assert value.strip(), f"{ctx}: field '{field}' must not be empty."
        else:
            assert value is not None, f"{ctx}: field '{field}' must not be null."
