# Strategy 1 — Genre Affinity

The first of the four recommendation strategies named in [`CLAUDE.md`](../CLAUDE.md). Single-hop: walk from a user, through their 4★+ ratings, to the genres of those movies, then back out to *other* movies in those genres that the user hasn't rated yet. Score by how strongly the user "likes" each matched genre.

Reference notebook: [`notebooks/11_strategy_genre_affinity.ipynb`](../notebooks/11_strategy_genre_affinity.ipynb).
Implementation: [`src/recommender.py`](../src/recommender.py) — `genre_affinity()` + `GENRE_AFFINITY_CYPHER`.

---

## What This Notebook Demonstrates

Sixteen cells, walking the strategy end-to-end on the recurring anchor user 196 (same anchor as notebooks 09 / 10 / 12). The first half builds the query in pieces (Phase 1 → Phase 2 → Phase 3 as standalone Cypher); the second half collapses them into the unified `GENRE_AFFINITY_CYPHER` constant, calls the wrapper, then explores the knobs and edge cases.

| # | Section | Takeaway |
|---|---|---|
| 0 | **Framing** | What "single-hop genre affinity" means, why the explainability shape is *global seeds + per-rec `matched_genres`* (not a per-rec chain). |
| 1 | **Setup** | Same `sys.path` + imports pattern as notebooks 04–10 / 12. Pulls `run_query` and `close_driver` only; `genre_affinity` is imported later (cell 9), once the phase-by-phase build has paid off. |
| 2 | **User 196's genre profile** | Standalone Cypher: top 5 genres by 4★+ count. Establishes what we *expect* Strategy 1 to surface. |
| 3 | **"Build the query phase by phase"** | Frame the next three cells: each phase ends with `RETURN` so it runs standalone; in cell 8's unified version those `RETURN`s become `WITH`. Direct callback to the `WITH` ↔ `RETURN` distinction from notebook 09. |
| 4 | **Phase 1 standalone** | Top 3 genres by 4★+ count, ending with `RETURN` over `(genre, affinity)`. Course-taker sees the top-genres list as data, not as a black-box intermediate. |
| 5 | **Phase 2 standalone** | Given Phase 1's top genres, surface up to 8 of user 196's ≥4★ seed titles bridging into those genres, with the list of top genres each seed sits in. Renders `(seed_title, in_genres)` — the evidence pool the unified query slices `[..5]` from. |
| 6 | **Phase 3 standalone** | Given top genres + seed pool, walk forward to unseen recs in those genres, aggregate per rec, score, rank. Same final shape as the wrapper function output. Rendered as DataFrame: `(title, year, score, matched_genres, seed_movies)`. |
| 7 | **"Now bring it all together"** | Markdown narrates the collapse: standalone `RETURN`s become `WITH`s, the final `RETURN` lives at the end of Phase 3. |
| 8 | **The unified constant** | `from recommender import GENRE_AFFINITY_CYPHER; print(GENRE_AFFINITY_CYPHER)`. The same Cypher the reader just ran in pieces, now visible as the one query that ships. |
| 9 | **Call the wrapper** | `genre_affinity(196)`. Renders identically to cell 6 — same `movieId`s in the same order. The function is just the parameter-passing wrapper. |
| 10 | **Reading the explainability shape** | Markdown: how to read one rec — `matched_genres` as the subset of top genres the rec sits in, `seed_movies` as the *shared* evidence pool across all recs. Why it's honest (Strategy 1's score aggregates over genres, not paths — a per-rec chain `seed → genre → rec` would mislead). Foreshadow Strategy 2 (notebook 12) where per-rec chains are the load-bearing shape. |
| 11 | **Knob — `top_n_genres`** | `=1` vs `=5`. Tighter = sharper per-rec story (all recs share one genre); wider = more multi-genre overlap and bigger scores. |
| 12 | **Knob — `threshold`** | `=3.0` vs `=4.5`. Lower = more permissive seed pool, blurrier affinity signal; higher = sharper but smaller candidate pool. |
| 13 | **Cold-start edge case** | (a) A user with zero 4★+ ratings → `[]`. (b) A non-existent user (99999) → `[]`. Contract: empty list = no signal. Strategy 4 owns the fallback. |
| 14 | **Anchor sanity** | Soft check: returned `movieId`s should not overlap with user 196's rated movies. Cypher counts the overlap; expected = 0. |
| 15 | **Cleanup** | `close_driver()`, same pattern as notebooks 04–10 / 12. |

Cell 10 is the load-bearing one — it teaches the reader how to *defend* the score to a stakeholder, and why Strategy 1's explainability shape is genres + global seeds rather than a per-rec chain.

---

## Scope Decisions

A few choices worth recording.

- **Score = `sum(affinity)` across matched top genres.** Not a weighted average; not popularity-normalized. A rec in 2 top genres outranks a rec in 1, weighted by how strong the user's affinity to each was. Honest aggregate — no calibration claimed. Future strategies (or Strategy 4 composite) can introduce normalization if Streamlit demos look off; Strategy 1 stays interpretable.
- **`top_n_genres` default = 3.** Tightens the per-rec story. Most users have 3–5 distinct genres in their 4★+ ratings, and 3 keeps the explanation crisp. The notebook's cell 11 shows what the knob does at `=1` and `=5` so a reader can build intuition.
- **Cold start returns an empty list.** Zero 4★+ ratings → empty `list[dict]`. No Python-side flag, no fallback inside Strategy 1. The "1-rating user still gets recs" teaching moment from [`CLAUDE.md`](../CLAUDE.md) lives in **Strategy 4** (composite with demographic pivots), where it fits naturally. Strategy 1 alone is honest about needing signal.
- **Explainability shape = global seeds, not per-rec chains.** Strategy 1's score is an *aggregate* (`sum(affinity)` over matched top genres), not a single path (`A → B → C`). Per-rec single-chain explanations would mislead — they'd imply a causal link the score doesn't support. So every rec carries `matched_genres` (which of the user's top genres it sits in) + `seed_movies` (up to 5 of the user's 4★+ titles in those genres) — *evidence* the affinity is real. Per-rec chains land in **Strategy 2** (director/actor multi-hop), where the structure of the query *is* the explanation.
- **Tie-break by `(score DESC, title ASC)`.** Simple, deterministic, no extra Cypher gymnastics. Popularity-weighted tie-breaks can come later if Strategy 4 wants them; Strategy 1 stays clean.
- **No APOC.** The query uses only plain `UNWIND`, `collect`, and the `[..5]` slice — works on AuraDB Free out of the box. If APOC isn't installed (it usually isn't on Free), nothing breaks.
- **No Python-side filtering or sorting.** Per [`CLAUDE.md`](../CLAUDE.md): *"All logic must be implemented as Cypher queries."* The `genre_affinity()` function is a thin parameter-passing wrapper around `GENRE_AFFINITY_CYPHER`. The verification step (`grep -nE "sort|filter|sorted|key=lambda"`) confirms the function itself has none.
- **Soft prints, no asserts.** Same policy as notebooks 08/09/10. The notebook is a teaching artifact, not a test. Cell 14's anchor sanity check prints `OK` or `MISMATCH` rather than raising.

---

## What's In vs. What's Out

| In scope | Out of scope | Where it lands |
|---|---|---|
| Genre affinity by 4★+ count | Genre affinity by rating *value* (e.g. mean rating) | Possibly Strategy 4 calibration; not yet |
| Tunable `top_n_genres`, `threshold` | Tunable score formula (weighted, normalized) | Strategy 4 if needed |
| Aggregate score + matched genres + seed movies | Per-rec single-chain explanation | **Strategy 2** ([T-20](#)) — director/actor multi-hop |
| Empty list on cold start | Demographic-pivot fallback for cold users | **Strategy 4** ([T-22](#)) — composite |
| `UNWIND`, `collect`, `[..5]` slice | `apoc.coll.*` helpers | Not needed |
| Read queries only | Write queries (`CREATE`, `MERGE`) | Notebooks 04 → 07 |
| Soft prints | Hard asserts / pytest | Out of project scope |
| Tie-break `(score DESC, title ASC)` | Popularity-weighted tie-breaks | Possibly Strategy 4 |

---

## Quick Sanity Check Before Running

If a cell errors on first run, it's almost always one of these:

1. **Notebooks 03 → 07 haven't been run against the current AuraDB instance.** Cell 2's profile query returns zeros — no data is loaded. Re-run the load notebooks.
2. **AuraDB instance paused.** Free-tier instances auto-pause; resume from [console.neo4j.io](https://console.neo4j.io).
3. **`.env` missing or stale.** `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` must point to the live instance.
4. **User 196 not in dataset.** Same recurring anchor as notebooks 09 / 10 / 12 — if those work, this will too.
5. **`from recommender import genre_affinity, GENRE_AFFINITY_CYPHER` fails.** [`src/recommender.py`](../src/recommender.py) must use `from graph import run_query` (not `from src.graph import …`), matching the notebook's `sys.path` setup. The T-19 implementation gets this right; older stubs may not.