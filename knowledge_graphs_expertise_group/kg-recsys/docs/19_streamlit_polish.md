# Streamlit — UX Polish (T-27)

Debugging reference for the cross-cutting UX polish layered onto the three demo screens. The screens themselves are documented in [docs/16](16_streamlit_user_profile.md) / [docs/17](17_streamlit_recommendation.md) / [docs/18](18_streamlit_graph_explorer.md); this doc covers what changed *across* them at T-27 and what to check when the polish layer itself misbehaves.

Implementation: [`app/streamlit_app.py`](../app/streamlit_app.py) — top-of-file `safe_run_query` wrapper, sidebar block, per-screen empty-state branches.

---

## What This Layer Adds

Four cross-cutting concerns the per-screen tasks (T-24/25/26) deliberately deferred:

1. **`safe_run_query` wrapper** — central error handling. Every fetcher routes Cypher through it instead of calling `run_query` directly. Catches `ServiceUnavailable` / `AuthError` / `Neo4jError` and renders an `st.error` with an actionable next step, then `st.stop()`s the current rerun.
2. **Spinner coverage gap on Screen 1** closed. `_fetch_ratings` now runs inside `st.spinner("Loading user {N}…")`, matching the existing spinners on Screens 2 and 3.
3. **First-load empty-state messages** on Screens 2 and 3. Before the user clicks `Get Recommendations` / `Search`, an `st.info` placeholder tells them what to do — the blank canvas was confusing on the first visit.
4. **Sidebar polish.** App title, one-line subtitle, per-screen caption under the radio (changes when you switch screens), and a `Clear all caches` button at the bottom.

`:COLLABORATED_WITH` rendering is **deliberately out of scope** for T-27 — the suspected pyvis edge-rendering bug between previously-existing nodes is its own investigation; the rest of T-27 doesn't depend on it.

---

## Scope Decisions Locked at T-27

- **One central wrapper, not per-screen try/except.** A single `safe_run_query(query, params)` sits at the top of the file; every fetcher passes Cypher through it. Reason: nine fetcher call sites; per-call try/except blocks would triple the screen logic and drift apart. The wrapper is the only place that knows about `neo4j.exceptions`.
- **`st.error` + `st.stop()`, not exception bubbling.** A bubbled exception in Streamlit renders a red traceback that's useless to a course participant. `st.error()` gives a clear message; `st.stop()` halts the rerun cleanly so the user doesn't see a half-drawn UI behind the error. Subsequent reruns retry, so the recovery path (resume AuraDB → click Clear all caches → rerun) works naturally.
- **Three caught error classes: `ServiceUnavailable`, `AuthError`, `Neo4jError`.** These cover the three failure modes that actually happen on free-tier Aura: instance auto-paused after idle, bad `.env`, query syntax / timeout. Anything else (unexpected Python errors, network exotica) still bubbles — those *should* surface a traceback because they're bugs, not operating-condition issues.
- **Wrapper is not cached.** The `@st.cache_data` decorators stay on the fetchers; the wrapper is plain Python. If the wrapper were cached, an error path would cache the `st.stop()` and prevent retry on the next rerun.
- **Spinner labels say what the system is doing, not just "Loading…".** Screen 1: `"Loading user {N}…"`; Screen 2: `"Running {strategy}…"`; Screen 3: `"Searching…"` and `"Building subgraph for {kind} '{label}'…"`. Specific labels surface where time is being spent on the slow cold-cache calls.
- **Empty-state messages on first load use `st.info`, not `st.markdown` or `st.caption`.** `st.info` gives the colored info-box that's visually distinct from the screen's own captions, so the user knows it's a system message ("do this next") not part of the result content.
- **Sidebar caption is per-active-screen, not per-radio-option.** `st.sidebar.radio` doesn't natively show captions per option (you'd need a custom widget). Showing the caption for the *active* screen below the radio gives one-line context with no extra widget code.
- **`Clear all caches` button uses `st.cache_data.clear()`**, not per-function `.clear()`. One button drops every cached fetcher result across all three screens. Matches the user's mental model: "the cache" is one thing, not three.
- **No multipage refactor (`st.navigation`) yet.** Three screens still fit in one file; multipage adds a separate-file-per-page convention plus its own state-handling rules that aren't worth the disruption at this scale. Defer until a 4th screen lands.
- **No user_id sync between Screens 1 and 2.** Sharing state between screens via `st.session_state` is plausible but has subtle Streamlit gotchas (widget keys vs. raw state). Out of scope for T-27; revisit if it becomes a real friction point.
- **Companion doc, no notebook.** Same rationale as docs/16-18 — this is a presentation-layer concern, not a Cypher teaching artifact.
- **`:COLLABORATED_WITH` edges deferred.** The pyvis edge-rendering question from T-26 is unrelated to UX polish; tracking separately.

---

## Troubleshooting / Quick Sanity Check

### 1. Error toast keeps firing every rerun
You see "Cannot reach Neo4j AuraDB…" on every interaction, even after you resumed the instance.
- **Cause:** the empty result from the failed call was cached before `safe_run_query` was added — or another fetcher is hitting a different paused state. The wrapper bypasses the cache on error (it calls `st.stop()` before returning), so a fresh error means the underlying problem is still there.
- **Fix:** confirm the instance is `Running` in [console.neo4j.io](https://console.neo4j.io), click **Clear all caches** in the sidebar, then rerun.

### 2. Sidebar `Clear all caches` button does nothing visible
The button click triggers a rerun, but the visual feedback is just the page refreshing. There's no toast.
- **Verify it ran:** edit a fetcher's Cypher, click the button, rerun — the new query results should appear. If they don't, `st.cache_data.clear()` may not be applying because Streamlit cached a higher-level component. Restart `streamlit run`.

### 3. First-load `st.info` placeholder won't go away after I click the button
- **Screen 2:** clicking `Get Recommendations` writes to `st.session_state.rec_payload`. If the placeholder persists, the button click never fired — check the terminal for a swallowed exception inside the strategy call.
- **Screen 3:** clicking `Search` writes to `st.session_state.explorer_candidates`. Same check.
- The placeholder uses `if payload is None:` / `if candidates is None:`. An empty list `[]` is not `None`, so an empty search result correctly falls through to the "no matches" branch, not the placeholder.

### 4. `st.stop()` swallowed a real bug I needed to see
The wrapper catches `Neo4jError` broadly — that includes Cypher syntax errors you might introduce while editing.
- **Symptom:** you edited a Cypher query, the app shows "Neo4j query error: …", but you want the full traceback.
- **Fix:** temporarily comment out the `except Neo4jError` branch and rerun; Streamlit will show the standard red traceback. Restore the branch when done.

### 5. Sidebar caption shows the wrong screen's description
The dict lookup is `_SCREEN_CAPTIONS[screen]`. If you renamed a screen in `SCREENS` without updating `_SCREEN_CAPTIONS`, you'll get a `KeyError`.
- **Fix:** keep the two in sync. Both are at the top of the file, adjacent — a screen rename should touch both lines.

### 6. Spinner shows on every keystroke in Screen 1
The spinner wraps `_fetch_ratings`, which is `@st.cache_data` keyed on `user_id`. Changing the number input triggers a rerun that may hit the cache — in which case the spinner flashes briefly. That's expected; the cache hit completes in milliseconds.
- If the spinner *lingers* for seconds on a user you've already loaded, the cache was invalidated (you clicked **Clear all caches**, restarted Streamlit, or the TTL expired). The next call is uncached and slow.

### 7. `AuthError` after rotating credentials
Streamlit's import-time singleton in [`src/graph.py`](../src/graph.py) holds the driver with the old credentials.
- **Fix:** restart `streamlit run`. Clearing the cache only clears `@st.cache_data` results, not the driver singleton.

### 8. Error toast wraps awkwardly on narrow viewports
`st.error` renders the message as plain text with markdown support. If the layout is mid-resize, the toast may wrap mid-link.
- Cosmetic only; the actionable text remains readable. Widen the viewport.

---

## Where the Code Lives

| Concern | Where |
|---|---|
| Central error wrapper | [`app/streamlit_app.py`](../app/streamlit_app.py) — `safe_run_query` (top of file, after imports) |
| Caught error classes | Same file, `from neo4j.exceptions import AuthError, Neo4jError, ServiceUnavailable` |
| Sidebar block | Same file, immediately after the wrapper — title, subtitle, radio, per-screen caption, Clear-caches button |
| Per-screen captions | Same file, `_SCREEN_CAPTIONS` dict |
| Screen 1 spinner | Same file, Screen 1 block — `with st.spinner(f"Loading user {user_id}…")` |
| Screen 2 first-load placeholder | Same file, Screen 2 block — `if payload is None: st.info(...)` |
| Screen 3 first-load placeholder | Same file, Screen 3 block — `if candidates is None: st.info(...)` |
| Driver singleton (untouched) | [`src/graph.py`](../src/graph.py) — `get_driver`, `run_query` |