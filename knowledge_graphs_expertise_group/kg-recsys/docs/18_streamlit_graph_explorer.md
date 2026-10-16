# Streamlit — Screen 3: Graph Explorer

Debugging reference for the third screen of the demo app — the "wow screen" that takes a free-form search and renders a local subgraph around any movie or actor in the catalog. The teaching for the underlying Cypher patterns lives in [notebooks/09_cypher_queries.ipynb](../notebooks/09_cypher_queries.ipynb) and [notebooks/07_collaborated_with.ipynb](../notebooks/07_collaborated_with.ipynb) (for the `:COLLABORATED_WITH` derived edge). This doc covers how the *screen* is wired and what to check when it misbehaves.

Implementation: [`app/streamlit_app.py`](../app/streamlit_app.py) — Screen 3 block.

---

## What This Screen Shows

A two-step flow:

1. **Search** — type any substring and click **Search**. The screen runs `MATCH (m:Movie) WHERE toLower(m.title) CONTAINS toLower($q)` UNION-ALLed with the same shape over `Actor.name`, capped at 10 hits per kind. Results render as a single selectbox so 20-candidate disambiguation is one click.
2. **Show Subgraph** — pick one candidate and click **Show Subgraph**. The screen fetches a *structured* local subgraph (multi-phase Cypher, per-edge-type caps) and renders it with pyvis.

The Movie entry point shows: the movie + its genres + director + top-5 billed actors + director's other films (5) + each marquee actor's other films (3 each, billing ≤ 3). Target: ~25-40 nodes.

The Actor entry point shows: the actor + top-5 movies they're billed in + each movie's director + 3 genres + top-3 co-actors + top-8 frequent collaborators via the derived `:COLLABORATED_WITH` edge (movie_count ≥ 3). Those collaborators are typically *already drawn* as per-movie co-actors — the COLLAB edges then form a light-blue web *between existing nodes*, which is exactly the point: the derived edge surfaces a relationship that the per-movie phase only implies. Target: ~30-45 nodes.

---

## Scope Decisions Locked at T-26

- **Two entity types only: Movie and Actor.** User / Genre / Occupation / Gender entry points are degenerate (hubs explode the depth-2 traversal). Director-as-entry was considered but folded out — directors are reachable from their movies in the Movie subgraph already.
- **Two-step search flow (Search → pick → Show Subgraph), not auto-render.** Reason: subgraph queries are heavy (3 sequential AuraDB round-trips) and we don't want to fire them on every keystroke. The user explicitly opts in.
- **Structured per-edge-type Cypher with explicit caps**, not generic depth-2 (`MATCH (n)-[*1..2]-(neighbor)`). Reason: the generic pattern explodes through hub nodes (Genre, popular Actor) — a 2-hop walk from "Tom Hanks" through `:FEATURES_ACTOR` → Movie → `:IN_GENRE` → Genre → `:IN_GENRE` → Movie returns thousands of nodes. The structured query gives a predictable ~30-node bundle.
- **`:COLLABORATED_WITH` drawn between existing nodes for Actor entry.** Top-8 frequent co-stars (movie_count ≥ 3), **no exclusion filter** — collaborators that are already in the subgraph (drawn as per-movie co-actors) get a light-blue COLLAB edge to the entry node; collaborators not yet drawn become new actor nodes. The first version filtered out already-drawn actors, which silently consumed all the edges for dense subgraphs like De Niro/Pesci. The "graph-y" payoff of the derived edge is precisely that it surfaces a relationship between actors the per-movie phase only *implies*.
- **One color per node label** (extending Screen 1's `_NODE_COLORS` palette). Genre = teal, Director = deep orange, Actor = purple. Entry-point node is bigger and bordered (`size=30`, `borderWidth=3`) so the user can find it instantly.
- **Edge labels show the relationship type** (`IN_GENRE`, `DIRECTED_BY`, `FEATURES_ACTOR`, `COLLAB ×N`). Tooltips on nodes add secondary detail (billing order, collaboration count, release year). Physics enabled — the layout is interactive, drag-to-rearrange.
- **Three-query split per subgraph rather than one mega-Cypher.** The big query would need `CALL { ... }` subqueries to handle "no actors" / "no director" edge cases without dropping the row. Three small queries with Python conditionals is clearer. Cache hits cover the cost.
- **Cache + session_state pattern, same as Screen 2.** Search results, candidate list, and rendered HTML all survive reruns via `st.session_state.explorer_*` keys. Clicking Show Subgraph doesn't re-query if the user just toggles the selectbox.
- **Companion doc, no notebook.** Same rationale as docs/16 and docs/17 — this is a presentation screen, not a teaching artifact.
- **Polish is T-27.** Functional first.

---

## Troubleshooting / Quick Sanity Check

### 1. AuraDB instance paused
Same as Screens 1 and 2 — see [docs/16 §1](16_streamlit_user_profile.md). Resume from console, **Clear cache** from the Streamlit menu, then **Rerun**.

### 2. `.env` missing or stale
Same as Screen 1. First search will raise `neo4j.exceptions.ServiceUnavailable`.

### 3. Search returns nothing for a term you expected to match
- Term is < 2 characters — guarded in `_search_candidates`. Try a longer substring.
- The data isn't loaded — `MATCH (m:Movie) RETURN count(m)` in Neo4j Browser should show 1,682 (MovieLens 100K). If zero, run loader notebooks 03 → 07.
- Substring is case-sensitive in your head but the query uses `toLower($q) CONTAINS toLower(...)` — it shouldn't be sensitive. Confirm the term is actually a substring of any title/name.
- Title in MovieLens has the year appended (`"Toy Story (1995)"`). Searching `"toy story"` works; searching `"1995"` matches dozens of titles.

### 4. Candidates show but "Show Subgraph" produces a blank canvas
- The picked entity has no neighbors. The warning message should fire; if it doesn't, check the terminal for a swallowed exception from `_fetch_*_subgraph`.
- pyvis wrote the HTML but the browser blocked it. Reload the page; check the dev console.

### 5. Subgraph is dense and unreadable
The per-edge-type caps (5 actors, 3 co-actor films, 5 collaborators, 3 genres) bound the size at ~30-45 nodes. If you're seeing more:
- You edited the Cypher and removed the `[..N]` slice or the `LIMIT`. Restore them.
- A single actor stars in many films and the underlying graph is dense — the subgraph is correct, just visually busy. Drag the entry-point node to a corner to spread things out.

### 6. `:COLLABORATED_WITH` edges missing on a famous actor
- The actor has no co-stars with movie_count ≥ 3 in the loaded data. MovieLens 100K is sparse; many actors only co-star once or twice. Sanity check in Browser: `MATCH (a:Actor {name: "<name>"})-[c:COLLABORATED_WITH]-() WHERE c.movie_count >= 3 RETURN count(c)`. If zero, drop the threshold in `_fetch_actor_subgraph` to `>= 2`, or pick a denser actor.
- The `:COLLABORATED_WITH` edges were never created. [notebook 07](../notebooks/07_collaborated_with.ipynb) must run before this screen produces them. Verify: `MATCH ()-[c:COLLABORATED_WITH]->() RETURN count(c)` in Browser — should be a few thousand.
- Edges *should* draw between actors already on screen (the dedup happens in the renderer, not the query — see the scope decision above on `:COLLABORATED_WITH`). If you see new actor nodes appearing but no edges between *existing* ones, the renderer's `seen` set check in `add_edge` is misbehaving — `print(seen)` from inside `_render_subgraph` to inspect.

### 7. Selectbox shows the candidate but `id` cast fails on Show Subgraph
Candidate `id` is returned as `toString(m.movieId)` from Cypher (so movies and actors share a single string column). The Python branch does `int(picked["id"])` for movies. If the cast fails, the candidate row is corrupted — clear the cache and re-search.

### 8. `KeyError: 'top_actors'` or similar inside the renderer
The bundle was returned by `_fetch_movie_subgraph` / `_fetch_actor_subgraph` but a phase didn't populate the expected key. Both fetchers initialize all keys (`[]` when empty) precisely so the renderer's `.get(key) or []` pattern is safe. If you see a KeyError, you've removed an `else: bundle["..."] = []` branch — restore it.

### 9. Slow first render
Expected. Cold cache + free-tier AuraDB + 3 sequential queries = 3-6 seconds for the Movie subgraph, slightly more for the Actor subgraph (the per-movie `UNWIND` adds work). The spinner is the progress indicator. Same input within 10 minutes returns from cache instantly.

### 10. Subgraph stale after editing the Cypher in `_fetch_*_subgraph`
`@st.cache_data` keyed on the function arguments — editing the query body doesn't invalidate. **Clear cache** from the Streamlit menu, then **Rerun**.

### 11. Search worked, then clicking "Show Subgraph" did nothing visible
- The button rerun completed but `st.spinner` blocked rendering of the subgraph. Wait for the spinner to clear.
- The button click landed on a candidate list that no longer includes the picked option (you re-searched in between). The selectbox value resets to the first option on rerun; check the current selection.

---

## Where the Code Lives

| Concern | Where |
|---|---|
| Screen rendering | [`app/streamlit_app.py`](../app/streamlit_app.py) — Screen 3 block |
| Candidate search | Same file, `_search_candidates` (cached, UNION ALL over Movie/Actor) |
| Movie subgraph fetch | Same file, `_fetch_movie_subgraph` (3 sequential queries) |
| Actor subgraph fetch | Same file, `_fetch_actor_subgraph` (3 sequential queries, includes `:COLLABORATED_WITH`) |
| pyvis network construction | Same file, `_render_subgraph` (branches on `kind`) |
| Color palette extension | Top of Screen 1 block — `_NODE_COLORS` dict (Genre/Director/Actor added at T-26) |
| Derived `:COLLABORATED_WITH` edge | [`notebooks/07_collaborated_with.ipynb`](../notebooks/07_collaborated_with.ipynb) — see [docs/07](07_collaborated_with.md) |
| Cross-rerun state | `st.session_state.explorer_candidates`, `.explorer_subgraph_html`, `.explorer_subgraph_label` |