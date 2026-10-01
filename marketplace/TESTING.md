# Testing Guide — DA CoE Plugin Marketplace

This repo ships a small, fast **PyTest** suite that validates the *structure,
schema, and naming conventions* of the marketplace catalog, every plugin manifest,
and every skill. Run it locally before opening a PR — it catches the mistakes CI
will otherwise reject: a malformed `marketplace.json`, a missing `SKILL.md`, a
name that doesn't match its directory, or a plugin that isn't registered.

The suite is **data-driven**: it walks the real repo tree and automatically tests
every plugin and skill it finds. **You do not edit any test files to cover a new
skill** — just add your skill correctly and it gets validated.

---

## Setup

From the repo root:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-test.txt
```

Dependencies are intentionally minimal: `pytest` + `PyYAML`.

---

## Running the tests

```bash
pytest                 # run everything (config lives in pytest.ini)
pytest -v              # verbose: shows one case per plugin and per skill
```

With `-v` you'll see per-item cases, e.g.:

```
tests/test_plugins.py::test_plugin_name_matches_directory[growth-optimization-analytics] PASSED
tests/test_skills.py::test_skill_name_matches_directory[weighting-experiment-metrics] PASSED
tests/test_skills.py::test_skill_name_matches_directory[exploratory-data-analysis] PASSED
```

### Running a subset

```bash
pytest tests/test_skills.py                     # only skill checks
pytest -k weighting-experiment-metrics          # only your skill (by name)
pytest -m marketplace                           # only marketplace catalog checks
```

Markers available: `marketplace`, `plugin`, `skill`.

**Iterating on a brand-new plugin, before it's registered in `marketplace.json`:**
registration now happens automatically (`python utils/marketplace_sync.py`,
run manually or by CI's `pr-validate.yml`), so a freshly-added plugin will
fail two catalog-registration checks until that sync runs. To validate
everything else about your new skill/plugin in the meantime:

```bash
pytest -k "not test_plugin_name_matches_marketplace and not test_catalog_and_disk_agree"
```

---

## What gets validated

| Area | File | Checks |
| :--- | :--- | :--- |
| Catalog | `.claude-plugin/marketplace.json` | valid JSON; required fields (`name`, `version`, `description`, `owner{name,email}`, `metadata{pluginRoot}`, `plugins[]`); SemVer version; valid owner email; each plugin entry has `name/source/description/category/tags`; `source` == `./plugins/<name>` and exists on disk; catalog and on-disk plugins agree (no orphans / unlisted) |
| Plugin manifest | `plugins/<id>/.claude-plugin/plugin.json` | valid JSON; required fields (`name`, `displayName`, `version`, `description`, `author{name,email}`, `keywords[]`); SemVer version; valid author email; `name` == directory == registered in catalog; has a non-empty `skills/` dir |
| Skill | `plugins/<id>/skills/<name>/SKILL.md` | frontmatter parses as YAML; required `name` + `description`; `name` is kebab-case and matches the directory; non-empty `description`; no unexpected frontmatter keys |

---

## Pre-PR checklist

1. **Add / update your skill** under
   `plugins/<plugin-id>/skills/<skill-name>/SKILL.md` with valid frontmatter
   (see the example below). The `name` must equal the folder name.
2. **Bump the plugin version** in `plugins/<plugin-id>/.claude-plugin/plugin.json`
   following [SemVer](https://semver.org/).
3. **If you're adding a whole new plugin**, `marketplace.json` registration is
   automatic — run `python utils/marketplace_sync.py` locally (or let CI's
   `pr-validate.yml` commit it for you) rather than hand-editing `plugins[]`.
4. **Run `pytest`** and make sure everything is green.
5. Open your PR.

---

## Example: a valid `SKILL.md`

```markdown
---
name: my-skill-name
description: One or more sentences describing what the skill does and when Claude should use it.
---

# My Skill

...skill instructions...
```

A long description may use a YAML folded block:

```markdown
---
name: my-skill-name
description: >
  A longer, multi-line description. The folded '>' style joins the lines into a
  single string, so you can wrap text for readability without changing the value.
---
```

---

## Common failures and how to fix them

| Message | Cause | Fix |
| :--- | :--- | :--- |
| `SKILL.md 'name' (...) must match the skill directory name (...)` | frontmatter `name` differs from the folder | make them identical (kebab-case) |
| `... must start with a YAML frontmatter block delimited by '---'` | missing/misplaced frontmatter | ensure the file starts with `---` on line 1 and closes with `---` |
| `'name' must be lowercase kebab-case` | uppercase/underscores/spaces in `name` | use `lower-case-hyphens` only |
| `unexpected frontmatter key(s) [...]` | non-standard frontmatter field | remove it, or add it to `ALLOWED_FRONTMATTER_FIELDS` in `tests/test_skills.py` if it's now official |
| `'version' must be SemVer X.Y.Z` | version isn't `X.Y.Z` | use e.g. `1.2.0` |
| `Plugins exist on disk but are not registered in marketplace.json` / `plugin '...' is not registered in marketplace.json` | new plugin dir not synced into the catalog yet | run `python utils/marketplace_sync.py` (or wait for CI's `pr-validate.yml` to do it and commit the result); while iterating, deselect these two checks — see "Running a subset" above |
| `'source' path does not exist on disk` | catalog `source` points nowhere | fix the path to `./plugins/<id>` |

---

## Suite layout

```
tests/
├── conftest.py          # fixtures + auto-discovery/parametrization of plugins & skills
├── helpers.py           # reusable validators (JSON/YAML loaders, type & format checks)
├── test_marketplace.py  # marketplace.json catalog checks
├── test_plugins.py      # plugin.json manifest checks (per plugin)
└── test_skills.py       # SKILL.md checks (per skill)
```

To extend validation (e.g. add a new required field), edit `helpers.py` for a
reusable check and reference it from the relevant `test_*.py` module.
