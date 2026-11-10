# Streamlit — Screen 2: Recommendation Engine

Debugging reference for the second screen of the demo app. The teaching for the four strategies lives in [notebooks/11–14](../notebooks/) and [docs/11–14](.). The unified dispatcher this screen calls is documented in [docs/15_unified_interface.md](15_unified_interface.md). This doc covers how the *screen* is wired and what to check when it misbehaves.

Implementation: [`app/streamlit_app.py`](../app/streamlit_app.py) — Screen 2 block.

---

## What This Screen Shows

Three inputs: **User ID** (default 196), **Strategy** (any of the four), **How many** recommendations to return (default 10).

Clicking **Get Recommendations** dispatches via `get_recommendations()` from [`src/recommender.py`](../src/recommender.py) and renders:

1. **Results table** — `title`, `year`, `score` (rounded to 3 decimals), sorted by score descending.
2. **Per-rec expanders** — one per recommendation, opens to that rec's strategy-specific explainability path. Shape depends on strategy:
   - **Genre Affinity** → `matched_genres`, `seed_movies`.
   - **Director / Actor Affinity** → `via_people`, `seed_chains` (already formatted as `seed → person → rec`).
   - **Collaborative Filtering** → `via_peers` (with overlap counts), `peer_chains` (already formatted as `shared → peer → rec`).
   - **Composite Multi-Signal** → `via_strategies`, `chains` (already formatted, one per contributing strategy).

If the wrapper returns `[]` (cold start, or all candidates filtered out), the screen shows an info message instead.

---

## Scope Decisions Locked at T-25

- **Button-gated.** Strategy fires only on "Get Recommendations" click — not on every widget change. Reason: CF and Composite queries are heavy; live re-query would spam AuraDB on every keystroke.
- **Goes through `get_recommendations()`, not `STRATEGIES` directly.** That's the unified surface from T-23. Future changes to dispatch (logging, rate-limiting) land in one place.
- **Strategy-specific kwargs hidden in MVP.** No `threshold` / `w_*` / `min_overlap` controls. The wrapper still accepts kwargs, so adding conditional widgets is T-27 polish.
- **Results cached with `@st.cache_data(ttl=600)`.** Same `(user_id, strategy, limit)` within 10 minutes returns instantly from cache, no AuraDB round-trip.
- **`st.session_state.rec_payload` survives reruns.** Streamlit reruns top-to-bottom on every widget interaction; without session_state, expanding a "Why?" expander would re-fire the strategy. The button writes the payload; subsequent reruns read from session_state.
- **One renderer per strategy.** `_render_explanation()` branches on the strategy display name and emits markdown. The four explanation shapes are too different to normalize cleanly (and we deliberately *didn't* normalize them in T-23 — see [docs/15](15_unified_interface.md)).
- **Score rounded to 3 decimals.** Genre Affinity uses summed ratings; Composite uses RRF fractions (~0.01–0.05). 3dp is readable for both.
- **No companion notebook.** The four strategies already have notebooks 11–14; this screen is presentation, not teaching.
- **Polish is T-27.** Functional first.

---

## Troubleshooting / Quick Sanity Check

### 1. AuraDB instance paused
See [docs/16 §1](16_streamlit_user_profile.md) — same fix. Resume from console, **Clear cache** from the Streamlit menu (top right), then **Rerun**.

### 2. `.env` missing or stale
Same as Screen 1. The first cached strategy call raises `neo4j.exceptions.ServiceUnavailable` if credentials are bad. Fix: check `.env`, relaunch `streamlit run`.

### 3. Strategy returns `[]` for a user that *should* have recs
- Loader notebooks (03 → 07) haven't been run against the current AuraDB instance — same issue as Screen 1.
- The strategy's internal filters excluded everything. **Genre Affinity** ignores genres with very few seed ratings; **Collaborative Filtering** requires a minimum overlap of shared ratings; **Composite** drops anything below the RRF score floor. These defaults are tuned for user 196's data shape; cold-start users with 1–2 ratings will see empty results from the multi-hop strategies. **Switch to Genre Affinity** — it has the most lenient cold-start behavior.

### 4. Cache giving stale results
You re-ran a loader notebook but Streamlit still shows the old recommendations.
- **Fix:** Streamlit menu (top right) → **Clear cache** → **Rerun**. Or restart `streamlit run`.

### 5. Button click does nothing
The script reruns but no spinner, no table, no error.
- The cached `_fetch_recommendations` call raised inside the spinner block and Streamlit swallowed the traceback. **Fix:** check the terminal where `streamlit run` is executing — uncaught exceptions surface there even when the UI hides them.

### 6. `ValueError: Unknown strategy '...'`
The selectbox can't produce this — the dropdown is bound to `STRATEGIES.keys()`. You'll only hit it if `STRATEGIES` was edited between Streamlit launches without restarting the app.
- **Fix:** restart `streamlit run`.

### 7. `TypeError: got an unexpected keyword argument '...'`
The screen doesn't pass any kwargs, so this shouldn't fire from the UI. If you see it, you're calling `_fetch_recommendations` from the REPL with a kwarg the strategy doesn't accept. See [docs/15](15_unified_interface.md) for the per-strategy parameter lists.

### 8. Expander opens but shows nothing
The rec has empty `seed_chains` / `peer_chains` / etc. — the underlying Cypher's `OPTIONAL MATCH` clauses all missed for this user.
- Happens for edge-case users with only one or two seed ratings. The rec is still valid (its `score` was computed), but the explainability path is degenerate.
- **Sanity check:** add `st.write(rec)` inside `_render_explanation` — confirm the explanation field is `[]` and not missing.

### 9. Expanders collapse when you change the user_id or strategy dropdown
By design. Changing the widget reruns the script and re-renders the expanders fresh; Streamlit doesn't preserve expander open/closed state across widget changes unless you wire it explicitly. Click the rec heading again to reopen.

### 10. Slow first run on Composite or Collaborative
Expected. Composite calls the other three inside a `CALL` subquery; Collaborative does a shared-rating overlap join. Cold cache + free-tier Aura = 3–8 seconds. The spinner indicates progress. Second click with identical inputs returns in milliseconds (cache hit).

### 11. Stale recs visible after changing inputs
The table and expanders show the *last* button click's results, even if you've since changed the user_id or strategy dropdown. That's the standard "search results don't auto-update" pattern. The subheader (`Top N via <strategy> (user <id>)`) tells you which click produced the visible rows. Click **Get Recommendations** again to refresh.

---

## Where the Code Lives

| Concern | Where |
|---|---|
| Screen rendering | [`app/streamlit_app.py`](../app/streamlit_app.py) — Screen 2 block |
| Cached strategy dispatch | Same file, `_fetch_recommendations` (wraps `get_recommendations`) |
| Explanation rendering | Same file, `_render_explanation` (branches on strategy name) |
| Unified `get_recommendations()` interface | [`src/recommender.py`](../src/recommender.py) — see [docs/15](15_unified_interface.md) |
| Strategy implementations | [`src/recommender.py`](../src/recommender.py) — see [docs/11–14](.) |
| Results payload (cross-rerun) | `st.session_state.rec_payload` — tuple `(recs, strategy_name, user_id)` |