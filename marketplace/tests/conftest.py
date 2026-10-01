"""Pytest fixtures and test discovery for the marketplace validation suite.

The suite is *data-driven*: it walks the real repo tree and parametrizes tests
over every plugin and skill it finds. Contributors never edit test files — adding
a valid skill or plugin simply adds new (green) test cases.

Key fixtures:
    repo_root         -> Path to the repository root.
    marketplace_json  -> parsed .claude-plugin/marketplace.json.
    plugin_dirs       -> list of plugins/<id>/ directories on disk.
    skill_dirs        -> list of plugins/<id>/skills/<name>/ directories on disk.

The ``pytest_generate_tests`` hook injects two parametrized fixtures:
    plugin_dir        -> one plugins/<id>/ directory per test case.
    skill_dir         -> one skill directory per test case.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from helpers import load_json

# Repo root is the parent of the tests/ directory containing this file.
REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS_ROOT = REPO_ROOT / "plugins"


def discover_plugin_dirs() -> list[Path]:
    """Every immediate subdirectory of plugins/ that holds a plugin manifest.

    A directory qualifies as a plugin if it contains .claude-plugin/plugin.json,
    so unrelated folders (or stray files) are ignored.
    """
    if not PLUGINS_ROOT.is_dir():
        return []
    return sorted(
        p
        for p in PLUGINS_ROOT.iterdir()
        if p.is_dir() and (p / ".claude-plugin" / "plugin.json").is_file()
    )


def discover_skill_dirs() -> list[Path]:
    """Every plugins/<id>/skills/<name>/ directory that contains a SKILL.md."""
    skill_dirs: list[Path] = []
    for plugin in discover_plugin_dirs():
        skills_root = plugin / "skills"
        if not skills_root.is_dir():
            continue
        skill_dirs.extend(
            sorted(s for s in skills_root.iterdir() if s.is_dir() and (s / "SKILL.md").is_file())
        )
    return skill_dirs


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def marketplace_path() -> Path:
    return MARKETPLACE_PATH


@pytest.fixture(scope="session")
def marketplace_json():
    """Parsed marketplace.json (fails clearly if missing or invalid)."""
    return load_json(MARKETPLACE_PATH)


@pytest.fixture(scope="session")
def plugin_dirs() -> list[Path]:
    return discover_plugin_dirs()


@pytest.fixture(scope="session")
def skill_dirs() -> list[Path]:
    return discover_skill_dirs()


def pytest_generate_tests(metafunc):
    """Parametrize tests over discovered plugins/skills.

    Each plugin/skill becomes its own test case, labelled by its directory name,
    so `pytest -v` shows a clear per-plugin / per-skill pass/fail breakdown.
    """
    if "plugin_dir" in metafunc.fixturenames:
        plugins = discover_plugin_dirs()
        metafunc.parametrize(
            "plugin_dir",
            plugins,
            ids=[p.name for p in plugins] or ["<no-plugins-found>"],
        )
    if "skill_dir" in metafunc.fixturenames:
        skills = discover_skill_dirs()
        metafunc.parametrize(
            "skill_dir",
            skills,
            ids=[s.name for s in skills] or ["<no-skills-found>"],
        )
