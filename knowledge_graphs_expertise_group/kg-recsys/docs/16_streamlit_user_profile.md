# Streamlit — Screen 1: User Profile

Debugging reference for the first screen of the demo app. The teaching material for the underlying Cypher lives in [notebooks/09_cypher_queries.ipynb](../notebooks/09_cypher_queries.ipynb) and [docs/09_cypher_queries.md](09_cypher_queries.md) — this doc covers how the *screen* is wired and what to check when it misbehaves.

Implementation: [`app/streamlit_app.py`](../app/streamlit_app.py) — Screen 1 block.

---

## What This Screen Shows

For the user picked in the sidebar number input (default `196`, the recurring anchor across notebooks 09-14), the screen renders two things:

1. **Rating History table** — every movie this user has rated, sorted by rating descending. Columns: title, year, rating, top-3 genres.
2. **Immediate KG Neighborhood** — a pyvis subgraph centered on the user, depth 1: their `:Occupation` node, `:Gender` node, and top-15 rated `:Movie` nodes, with the relationship type shown on each edge.

If the picked user has no ratings (cold-start or out-of-range ID), the screen shows an info message and skips both renders.

---

## Scope Decisions Locked at T-24

- **Single-file app, sidebar radio for navigation.** Three screens fit comfortably in one file. Multipage refactor deferred until any one screen grows past that.
- **Driver lifecycle relies on the module-level singleton in [`src/graph.py`](../src/graph.py).** `@st.cache_resource` not used here — would have added Streamlit as a hard dependency of `graph.py`, which the notebooks also import.
- **Read queries are cached with `@st.cache_data(ttl=600)`.** Same user_id within ten minutes returns instantly from cache, no AuraDB round-trip.
- **Default user is 196**, matching notebooks 09-14 for demo continuity.
- **Neighborhood = depth 1.** All three edge types off `:User` (`:RATED`, `:HAS_OCCUPATION`, `:HAS_GENDER`) are included, capped at top-15 movies by rating.
- **No slider for top-N.** Fixed at 15. Adding a control is T-27 polish.
- **No companion notebook.** Streamlit screen, not a Cypher teaching artifact.
- **Polish is T-27.** This task ships *functional*, not pretty.

---

## Troubleshooting / Quick Sanity Check

If the screen errors or shows nothing useful, check in this order:

### 1. AuraDB instance paused
Free-tier instances auto-pause after a few days idle. The first cached query of the session will return nothing or hang.
- **Fix:** resume from [console.neo4j.io](https://console.neo4j.io), then in the Streamlit menu (top right) → **Clear cache** → **Rerun**. Without the cache clear, Streamlit may keep returning the empty result it captured while the DB was down.

### 2. `.env` missing or stale
`NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` are loaded by `src/graph.py` at first import. If they're missing or point to a dead instance, the import succeeds but every query raises.
- **Symptom:** the import line at the top of `streamlit_app.py` works, but the first table render shows a `neo4j.exceptions.ServiceUnavailable` traceback.
- **Fix:** check `.env`, re-launch `streamlit run`.

### 3. No data loaded
The ratings query returns `[]` for *every* user.
- **Symptom:** the info message fires for any user_id, even 196.
- **Fix:** the loader notebooks (03 → 07) haven't been run against the current AuraDB instance. Re-run them in order.

### 4. Cache giving stale results
You re-ran a loader notebook (added/removed ratings) but Streamlit still shows the old counts.
- **Fix:** Streamlit menu (top right) → **Clear cache** → **Rerun**. Or restart `streamlit run`.

### 5. pyvis subgraph not rendering (blank box)
`components.html(...)` shows a 520px-tall empty area.
- **Likely cause:** the temp HTML file was written but the browser silently failed to parse it, usually because the chosen user has zero rated movies AND no occupation/gender (so the network has one isolated node and pyvis renders an empty canvas).
- **Check:** print `bundle` from `_fetch_neighborhood` — if every field is `None`, the user genuinely has no neighborhood.

### 6. "User N has no ratings" for a user you expected to have ratings
- The user_id was loaded but the `:RATED` edges weren't. Re-run [notebooks/05_load_relationships.ipynb](../notebooks/05_load_relationships.ipynb).
- The user_id is outside 1-943. The number_input enforces the range, but if you bypass it the empty branch fires.

### 7. `ModuleNotFoundError: No module named 'graph'` (or `'recommender'`)
The `sys.path.insert` line at the top of `streamlit_app.py` puts `src/` on the path so the app can `from graph import run_query` and `from recommender import STRATEGIES, get_recommendations`. The path is computed from `__file__` (an absolute path), so cwd doesn't matter — this works from any directory.
- **Why `src/` and not the repo root:** the convention across this repo (notebooks included) is that **`src/` is the import root** for project modules. `src/recommender.py` itself does `from graph import run_query`, not `from src.graph import ...`. The Streamlit app must follow the same convention so both layers agree on how to find `graph`.
- **Fix:** restore the import block at the top of `streamlit_app.py`:
  ```python
  sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
  from graph import run_query
  from recommender import STRATEGIES, get_recommendations
  ```

### 8. Pyvis writes to a temp file — is that safe?
Yes. `tempfile.NamedTemporaryFile(delete=False, suffix=".html")` writes to the OS temp directory, the file is read once into the HTML payload, and the OS cleans it up. We do not delete it explicitly because pyvis sometimes lazy-loads sidecar JS from the same path.

---

## Where the Code Lives

| Concern | Where |
|---|---|
| Screen rendering | [`app/streamlit_app.py`](../app/streamlit_app.py) — Screen 1 block |
| Cypher queries | Same file, `_fetch_ratings` and `_fetch_neighborhood` functions (cached) |
| pyvis network construction | Same file, `_render_neighborhood` function |
| Neo4j driver / singleton | [`src/graph.py`](../src/graph.py) — `get_driver`, `run_query` |
| Color palette for node types | Top of Screen 1 block — `_NODE_COLORS` dict |