# Strategy 4 — Composite Multi-Signal

The fourth and final recommendation strategy named in [`CLAUDE.md`](../CLAUDE.md). Composite multi-signal fuses Strategies 1, 2, 3 into a single ranked list via **weighted Reciprocal Rank Fusion**: each sub-strategy fetches its top `inner_k` recs, the composite discards raw scores and keeps only rank position, then scores each rec as the weighted sum of `1/rank` across contributing strategies. The query reuses the three existing constants via `CALL { ... }` subqueries — sub-strategy changes propagate to the composite for free. Each rec carries paired `via_strategies` + `chains` for per-strategy explainability.

Reference notebook: [`notebooks/14_strategy_composite_multi_signal.ipynb`](../notebooks/14_strategy_composite_multi_signal.ipynb).
Implementation: [`src/recommender.py`](../src/recommender.py) — `composite_multi_signal()` + `COMPOSITE_CYPHER`.
Companion strategies: [`docs/11`](11_strategy_genre_affinity.md), [`docs/12`](12_strategy_director_actor.md), [`docs/13`](13_strategy_collaborative_filtering.md).

---

## What This Notebook Demonstrates

Sixteen cells, walking the strategy end-to-end on the recurring anchor user 196 (same anchor as notebooks 09 / 10 / 11 / 12 / 13). The first half builds the query in pieces — each of the three sub-strategies wrapped with rank-attachment, plus a fourth merge phase, all as standalone Cypher. The second half collapses them into the unified `COMPOSITE_CYPHER` constant, calls the wrapper, then explores the knobs and edge cases.

| # | Section | Takeaway |
|---|---|---|
| 0 | **Framing** | What weighted RRF is and why rank-based normalization beats raw-score weighting; why `1/rank` (front-heavy, no smoothing constant); why `via_strategies` + `chains` (paired lists, one chain per contributing strategy); cold-start out of scope (filed as T-22b). |
| 1 | **Setup** | Same `sys.path` + imports pattern as notebooks 04–13. Pulls the three sub-strategy functions for cell 2's overlap diagnostic. `composite_multi_signal` is imported later (cell 10), once the phase-by-phase build has paid off. |
| 2 | **Three candidate pools** | Calls each sub-strategy with `k=15`, then renders a pool-sizes + pairwise/three-way-overlap + union table. Establishes the empirical motivation for fusion: the three signals overlap less than one might expect. |
| 3 | **"Build the query phase by phase"** | Frame the next four cells: each phase is one of the three sub-strategies wrapped with `collect` + `UNWIND range(...)` for rank attachment, ending with `RETURN`. Cell 7 wraps phases 1 / 2 / 3 as `CALL { ... }` subqueries inside one block. |
| 4 | **Phase 1 standalone** | The full `GENRE_AFFINITY_CYPHER` body with `$k=15`, plus rank attachment. Renders DataFrame: `(rank, title, year, chain)`. Reader sees Strategy 1's contribution to the composite as data. |
| 5 | **Phase 2 standalone** | Same shape for `DIRECTOR_ACTOR_CYPHER`. Renders Strategy 2's candidate pool ranked and chained. |
| 6 | **Phase 3 standalone** | Same shape for `COLLABORATIVE_CYPHER`. Renders Strategy 3's candidate pool ranked and chained. |
| 7 | **Phase 4 standalone — the merge** | Three `CALL { ... }` subqueries inline, union the three rank-lists, group by `movieId`, weighted RRF score with default `(1.0, 1.0, 1.0)` weights, build `via_strategies` + `chains`. Renders DataFrame matching the wrapper output. The load-bearing pedagogical cell — the reader sees the fusion happen as data. |
| 8 | **"Now bring it all together"** | Markdown narrates the collapse: each subquery in cell 7 corresponds to a constant in [`src/recommender.py`](../src/recommender.py) string-substituted at module load — `$k` → `$inner_k` and wrapped in `CALL { ... }`. |
| 9 | **The unified constant** | `from recommender import COMPOSITE_CYPHER; print(COMPOSITE_CYPHER)`. The reader sees the assembled Cypher — three subqueries + merge — as one printed block. Same Cypher they just ran in pieces. |
| 10 | **Call the wrapper** | `composite_multi_signal(196)`. Renders identically to cell 7 — same `movieId`s, same scores, same order. The function is just the parameter-passing wrapper. |
| 11 | **Reading the explainability chain** | Markdown: how to read one rec — `via_strategies` as the contributing sub-strategies, `chains` as the per-strategy explanations, the `zip()`-safe pairing. Score math walked through end-to-end (e.g. `1.0/2 + 1.0/4 = 0.75` for a rec at #2-in-genre and #4-in-collaborative). Two caveats: scores are not commensurable across users, and `chains[i]` is the explanation for `via_strategies[i]`. |
| 12 | **Knob — weights** | `(w_genre=3.0, others=1.0)` vs `(w_collab=3.0, others=1.0)`. The "I trust signal X more than signal Y" knob — top recs visibly shift toward the up-weighted strategy. |
| 13 | **Knob — `inner_k`** | `=5` vs `=50`. Tight pool: fewer recs survive to the merge. Wide pool: tail-position recs get into the merge with tiny `1/rank` contributions. The default `=15` trades coverage against signal-to-noise. |
| 14 | **Cold-start edge case + anchor sanity** | (a) Non-existent user (99999) → `[]`. (b) A user with zero ≥4★ ratings → `[]`. (c) Anchor sanity: returned `movieId`s do not overlap with user 196's rated movies. Contract: empty list = cold start at the composite level; demographic-pivot fallback is filed as T-22b. |
| 15 | **Cleanup** | `close_driver()`, same pattern as notebooks 04–13. |

Cells 7 and 11 are the load-bearing ones. Cell 7 is the pedagogical climax — the reader sees the fusion as data, end-to-end, before the wrapper is revealed. Cell 11 is the explanatory one — it teaches the reader how to defend a composite rec by attributing it to its contributing strategies and reading two (or three) chains side-by-side.

---

## Scope Decisions

A few choices worth recording.

- **Why rank-based normalization (RRF).** Raw scores from Strategies 1 / 2 / 3 sit on incompatible scales (genre affinity counts: 5–60; director/actor counts: 2–40; collaborative combined-products: 50–500+). Any linear-weighted-sum of raw scores is dominated by Strategy 3 regardless of weights — the bigger numbers win every time. Rank discards the magnitude question entirely: each strategy contributes a ranked list, the composite reads only position. RRF is scale-free, well-known, and easy to teach.
- **Why `1/rank` (no smoothing constant).** Front-heavy: rec #1 contributes 1.0 to its strategy, #2 contributes 0.5, #15 contributes ~0.067. A rec that hits #1 in one strategy beats a rec that hits #5 in all three. Simpler than the textbook RRF formula `1/(60 + rank)` — at notebook scale we want clarity over robustness to rank-list-length differences.
- **Why weights as parameters with `1.0` defaults.** Equal-weight neutral default makes "the composite is balanced" the baseline claim; reweighting is then a deliberate act the notebook can demonstrate (cell 12) and justify. Same teaching pattern as `min_overlap`, `top_n_peers`, `top_n_genres` in notebooks 11–13 — knobs the reader can turn to observe what changes.
- **Why `via_strategies` + `chains` (paired lists).** Honest per-strategy attribution. A rec surfaced by both *genre* and *collaborative* deserves to expose both chains; a rec surfaced by only one strategy exposes one chain. The two lists are built from the same `contributions` list comprehension in the same iteration order, so a reader can `zip(via_strategies, chains)` safely. Honest aggregate; no claim that the chains have been ranked by contribution.
- **One chain per contributing strategy.** Strategy 1's chain: `head(matched_genres) + ' → ' + head(seed_movies) + ' → ' + title`. Strategy 2's: `head(seed_chains)`. Strategy 3's: `head(peer_chains)`. Mirrors each sub-strategy's existing chain shape rather than inventing a unified format — the reader who's already seen 11 / 12 / 13 immediately recognizes the chain type by its shape.
- **Why `CALL { ... }` subqueries reusing existing constants.** DRY. The three sub-strategy bodies are unchanged; the composite version substitutes only the outer `LIMIT` parameter (`$k` → `$inner_k`) and wraps each in `CALL { }`. A fix to Strategy 1's body propagates to the composite for free. Single Cypher round-trip; all logic in Cypher per [`CLAUDE.md`](../CLAUDE.md).
- **Why `inner_k = 15` default.** Wide enough to surface recs that hit the long tail in one strategy but the head in another; tight enough that tail-position recs don't dilute the score with tiny `1/rank` contributions. Cell 13 makes the trade-off visible at `=5` and `=50`.
- **Why `$k` → `$inner_k` substitution at module-load.** The composite needs its own outer `LIMIT $k`; reusing the constants verbatim would collide on `$k`. The substitution is safe — `$k` appears exactly once in each constant, as the final `LIMIT`. The module-load verification (`COMPOSITE_CYPHER.count("LIMIT $k") == 1`, `count("LIMIT $inner_k") == 3`) confirms it.
- **Cold start returns `[]`.** Same contract as Strategies 1 / 2 / 3. If all three sub-strategies return empty, all three `collect()`s yield empty lists, the union is empty, the final `UNWIND` on empty yields no rows, and `RETURN` is empty. No Python-side check needed. The demographic-pivot fallback (the *"user with 1 rating still gets recs"* teaching moment from [`CLAUDE.md`](../CLAUDE.md)) is **filed as T-22b**, not delivered by T-22.
- **Partial cold start degrades gracefully.** If only one or two sub-strategies return results, the others contribute zero rows to the union. Recs from the live sub-strategies still get ranked and returned, with `via_strategies` listing only the strategies that surfaced them. No special handling needed; the union collapses naturally.
- **No APOC.** Enumeration via `UNWIND range(0, size(list) - 1) AS i`, fusion via `collect` + list concatenation + list comprehensions, scoring via `reduce()` + `CASE`. All in core Cypher 5. Works on AuraDB Free out of the box.
- **No Python-side filtering or sorting.** Per [`CLAUDE.md`](../CLAUDE.md): *"All logic must be implemented as Cypher queries."* The `composite_multi_signal()` function is a thin parameter-passing wrapper around `COMPOSITE_CYPHER`. The verification step (`grep -nE "sort|filter|sorted|key=lambda"` against the new function body) confirms it has none.
- **Tie-break by `(score DESC, title ASC)`.** Same as Strategies 1 / 2 / 3; simple, deterministic, no extra Cypher gymnastics. Popularity-weighted tie-breaks belong to Streamlit if a user ever asks for them.
- **Renamed `recommend_composite` → `composite_multi_signal`.** Matches the rename pattern from T-19 / T-20 / T-21 (`recommend_genre` → `genre_affinity`, `recommend_director_actor` → `director_actor_affinity`, `recommend_collaborative` → `collaborative_filtering`) and the `STRATEGIES` dict label `"Composite Multi-Signal"`.
- **Soft prints, no asserts.** Same policy as notebooks 08–13. The notebook is a teaching artifact, not a test. Cell 14's anchor sanity check prints `OK` or `MISMATCH` rather than raising.

---

## What's In vs. What's Out

| In scope | Out of scope | Where it lands |
|---|---|---|
| Weighted RRF fusion (`sum(w_s / rank_s)`) | Min-max or score÷max normalization | Out — RRF is the simpler answer for incompatible-scale signals |
| `$inner_k` as a parameter (default 15) | Strategy-specific `inner_k` (e.g. `inner_k_genre`, `inner_k_collab`) | Not needed at notebook scale |
| Per-rec `via_strategies` + `chains` (paired lists) | Per-rec score breakdown (e.g. `score_by_strategy: dict`) | Possibly Streamlit; not yet |
| Three sub-strategies as `CALL { ... }` subqueries | Materializing strategy outputs to disk and ranking offline | Out of project scope |
| Empty list on cold start (all three empty) | Demographic-pivot fallback for cold users | **T-22b** — separate task |
| Equal-weight `(1.0, 1.0, 1.0)` defaults | Learned / calibrated weights | Out per [`CLAUDE.md`](../CLAUDE.md) — no ML |
| `1/rank` formula | Smoothed RRF `1/(60 + rank)` | Out — clarity over robustness |
| Read queries only | Write queries (`CREATE`, `MERGE`) | Notebooks 04 → 07 |
| Soft prints | Hard asserts / pytest | Out of project scope |
| Tie-break `(score DESC, title ASC)` | Popularity-weighted tie-breaks | Possibly Streamlit |

---

## Quick Sanity Check Before Running

If a cell errors on first run, it's almost always one of these:

1. **Notebooks 03 → 07 haven't been run against the current AuraDB instance.** Cell 2's three-pool diagnostic returns zeros — no data is loaded. Re-run the load notebooks.
2. **AuraDB instance paused.** Free-tier instances auto-pause; resume from [console.neo4j.io](https://console.neo4j.io).
3. **`.env` missing or stale.** `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` must point to the live instance.
4. **User 196 not in dataset.** Same recurring anchor as notebooks 09 / 10 / 11 / 12 / 13 — if those work, this will too.
5. **`from recommender import composite_multi_signal, COMPOSITE_CYPHER` fails.** [`src/recommender.py`](../src/recommender.py) must use `from graph import run_query` (matching the notebook's `sys.path` setup), and the three existing constants (`GENRE_AFFINITY_CYPHER`, `DIRECTOR_ACTOR_CYPHER`, `COLLABORATIVE_CYPHER`) must still exist — the composite assembles them at module-load via string substitution.
6. **Empty result at default knobs.** If `composite_multi_signal(user)` returns `[]`, check each sub-strategy individually first: `genre_affinity(user)`, `director_actor_affinity(user)`, `collaborative_filtering(user)`. If all three return `[]`, that's the cold-start contract — not a bug. T-22b will address with demographic pivots.
