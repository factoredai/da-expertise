# Strategy 3 — Collaborative Filtering

The third of the four recommendation strategies named in [`CLAUDE.md`](../CLAUDE.md). User-mediated multi-hop: walk from a user, through their 4★+ ratings, to **peer users** who rated the same movies 4★+, then back out to *other* movies those peers also rated 4★+ — movies the anchor user hasn't seen. Peers are defined by a *hybrid* rule (an overlap floor plus a volume cap), the score is a *combined product* over (peer overlap × peer rating of the rec), and the explanation for one rec is a per-rec user-mediated chain. Same query shape as Strategy 2; different bridging entity, different question.

Reference notebook: [`notebooks/13_strategy_collaborative_filtering.ipynb`](../notebooks/13_strategy_collaborative_filtering.ipynb).
Implementation: [`src/recommender.py`](../src/recommender.py) — `collaborative_filtering()` + `COLLABORATIVE_CYPHER`.

---

## What This Notebook Demonstrates

Sixteen cells, walking the strategy end-to-end on the recurring anchor user 196 (same anchor as notebooks 09 / 10 / 11 / 12). The first half builds the query in pieces (Phase 1 → Phase 2 → Phase 3 as standalone Cypher); the second half collapses them into the unified `COLLABORATIVE_CYPHER` constant, calls the wrapper, then explores the knobs and edge cases.

| # | Section | Takeaway |
|---|---|---|
| 0 | **Framing** | What "user-mediated multi-hop" means, why the peer pool is hybrid (floor + cap), why the score is a combined product, why explainability is a per-rec peer chain. |
| 1 | **Setup** | Same `sys.path` + imports pattern as notebooks 04–12. Pulls `run_query` and `close_driver` only; `collaborative_filtering` is imported later (cell 9), once the phase-by-phase build has paid off. |
| 2 | **User 196's peer profile** | Standalone Cypher: top 10 peers of user 196 by overlap (shared ≥4★ titles). Establishes what we *expect* Strategy 3 to surface. |
| 3 | **"Build the query phase by phase"** | Frame the next three cells: each phase ends with `RETURN` so it runs standalone; in cell 8's unified version those `RETURN`s become `WITH`. Direct callback to the `WITH` ↔ `RETURN` distinction from notebook 09. |
| 4 | **Phase 1 standalone** | The full peer-finding block (post-aggregation `WHERE overlap >= min_overlap`, then `ORDER BY overlap DESC LIMIT top_n_peers`), ending with `RETURN` over `(peer_id, overlap, n_shared_titles)`. Reader sees the peer pool as data, not as a black-box intermediate. |
| 5 | **Phase 2 standalone** | Given Phase 1's top peers, unwind and surface their ≥4★ unseen-by-u recs *at row level*. Renders DataFrame: `(rec_title, peer_id, peer_rating, overlap)` — the row-level evidence Phase 3 will aggregate over. |
| 6 | **Phase 3 standalone** | Given the row-level evidence, group by rec, compute `sum(overlap × peer_rating)`, build `via_peers` + `peer_chains`, return ranked. Same final shape as the wrapper function output. Rendered as DataFrame: `(title, year, score, via_peers, peer_chains)`. |
| 7 | **"Now bring it all together"** | Markdown narrates the collapse: standalone `RETURN`s become `WITH`s, the final `RETURN` lives at the end of Phase 3. |
| 8 | **The unified constant** | `from recommender import COLLABORATIVE_CYPHER; print(COLLABORATIVE_CYPHER)`. The same Cypher the reader just ran in pieces, now visible as the one query that ships. |
| 9 | **Call the wrapper** | `collaborative_filtering(196)`. Renders identically to cell 6 — same `movieId`s in the same order. The function is just the parameter-passing wrapper. |
| 10 | **Reading the explainability chain** | Markdown: how to read one rec — `via_peers` as the contributing peers with overlap counts visible (so bridge strength is judgeable at a glance), one `peer_chain` narrated end-to-end in prose. Why Strategy 3's chain answers *"because people like you loved it"* (vs. Strategy 2's *"because of this director/actor"*). Two caveats: `score` is a ranking signal not a confidence percentage, `peer_chains` is order-by-unwind not strength-ranked. |
| 11 | **Knob — `min_overlap`** | `=1` vs `=10`. The noise-vs-quality teaching moment: at `=1`, random-coincidence peers flood in and recs become popularity-driven; at `=10`, the peer pool shrinks (possibly empty for thin users) and recs are tighter but fewer. |
| 12 | **Knob — `top_n_peers`** | `=5` vs `=100`. Tighter cap = shorter `via_peers` lists and fewer total recs; looser cap = tail peers contribute weak votes that dilute the score. Cell also calls out the cap × floor interaction. |
| 13 | **Cold-start edge case** | (a) A user with zero 4★+ ratings → `[]`. (b) A non-existent user (99999) → `[]`. Contract: empty list = no signal. Strategy 4 owns the fallback. |
| 14 | **Anchor sanity** | Soft check: returned `movieId`s should not overlap with user 196's rated movies. Cypher counts the overlap; expected = 0. |
| 15 | **Cleanup** | `close_driver()`, same pattern as notebooks 04–12. |

Cell 10 is the load-bearing one — it teaches the reader the contrast between Strategy 2's person-mediated chain (*"because of this director/actor"*) and Strategy 3's user-mediated chain (*"because people like you loved it"*), which is the payoff that justifies running the two strategies as separate signals rather than collapsing them.

---

## Scope Decisions

A few choices worth recording.

- **Hybrid peer definition: minimum-overlap floor *and* top-N peer cap.** Pure-threshold would sweep in a long tail of 1- or 2-movie peers from power users; pure top-N would let random-coincidence peers in for thin users. Defaults: `min_overlap = 3`, `top_n_peers = 25`. The floor kills noise; the cap prevents long-tail dilution. Both become notebook knobs in cells 11 and 12 — the cell where the reader drops `min_overlap` from 3 → 1 and watches garbage flood in is the teaching moment.
- **`min_overlap = 3` default.** Sharing 1 movie is basically random co-occurrence; 2 starts to be a weak signal; 3 is the minimum that survives the "could be coincidence" test for ML100K's density. Cell 11's `=1` experiment makes the noise floor visible.
- **`top_n_peers = 25` default.** Wide enough to surface diverse recs but tight enough that tail peers don't dilute the score. Cell 12 shows the trade-off at `=5` and `=100`.
- **Score = `sum(peer.overlap × peer.rating_of_rec)`.** Combined product. A peer who overlaps with the user on 12 movies and gave the rec 5★ contributes 60; a peer who overlaps on 3 and gave it 4★ contributes 12. Direct mirror of Strategy 1/2's `sum(affinity)` shape — same multiplier-over-collected-list pattern — keeping the three strategies comparable when Strategy 4 weights them. Both ingredients are load-bearing: rating-only throws away peer-strength signal, overlap-only throws away how much the peer actually liked the rec. Honest aggregate; no calibration claimed.
- **Overlap counted from ≥-threshold ratings on both sides.** Peers are defined by *shared positive taste*, not shared exposure. Two users who both watched and disliked the same movies aren't peers in any useful sense, and the "similar users also loved this" framing collapses if "peer" includes shared dislikes.
- **Per-rec `via_peers` + `peer_chains` (capped at 3).** Strategy 3's score, like Strategy 2's, is a path-based aggregate — every contribution comes from a concrete `(seed, peer, rec)` triple, so per-rec single-chain explanations honestly mirror the query. `via_peers` is a list of `{peer_id, overlap}` records — overlap is exposed so a stakeholder can judge bridge strength at a glance (5 peers each overlapping on 12 is a much stronger endorsement than 1 peer overlapping on 3). `peer_chains` is capped at 3 — enough evidence without UI noise.
- **`head(c.shared)` for each chain — arbitrary shared title per peer.** Shared titles are evidence, not ranked output. We don't claim "this is the *strongest* shared title for this peer" — only "here's one ≥4★ movie this peer and the anchor both loved." If reproducibility ever matters (e.g. Strategy 4 calibration), we can `ORDER BY` shared titles inside Phase 1.
- **`peer_chains` is order-by-unwind, not strength-ranked.** Peers are unwound in `overlap DESC` order, so position-1 chain comes from the highest-overlap peer, not necessarily the one whose rating contributed the most score. The `[..3]` slice inherits that order. All three chains are real; a reader inspecting `peer_chains` shouldn't infer position-1 is the "strongest contribution" — only that it comes from the highest-overlap bridge.
- **`toString(c.peer_id)` in the chain string.** `peer.userId` is an integer property; Cypher string concatenation requires an explicit cast. Same pattern Strategy 4 will likely repeat.
- **No `elementId()`.** Strategy 2 used `elementId()` to disambiguate `:Director` vs `:Actor` nodes by reference when carrying them through `WITH`. Strategy 3 doesn't need it — `userId` is already a unique integer property on `:User`, so peers can be matched by their `userId` directly. Simpler.
- **`NOT EXISTS { (u)-[:RATED]->(rec) }` excludes any rated movie, regardless of rating value.** Even movies the user disliked (1★ or 2★) are excluded from recs — we never recommend something the user has already formed an opinion on.
- **Cold start returns an empty list.** Same contract as Strategies 1 and 2. Zero ≥-threshold ratings → no peers found → empty `top_peers` collection → `UNWIND top_peers` in Phase 2 has nothing to expand → `[]`. No Python-side check needed. The "1-rating user still gets recs" teaching moment from [`CLAUDE.md`](../CLAUDE.md) lives in **Strategy 4** (composite with demographic pivots).
- **Tie-break by `(score DESC, title ASC)`.** Same as Strategies 1 and 2; simple, deterministic, no extra Cypher gymnastics. Popularity-weighted tie-breaks can come later in Strategy 4 if needed.
- **No APOC.** Plain `UNWIND`, `collect`, `reduce()`, list comprehensions, `head()`, `toString()`, and the `[..3]` slice — all in core Cypher 5. Works on AuraDB Free out of the box.
- **No Python-side filtering or sorting.** Per [`CLAUDE.md`](../CLAUDE.md): *"All logic must be implemented as Cypher queries."* The `collaborative_filtering()` function is a thin parameter-passing wrapper around `COLLABORATIVE_CYPHER`. The verification step (`grep -nE "sort|filter|sorted|key=lambda"` against the new function body) confirms it has none.
- **Soft prints, no asserts.** Same policy as notebooks 08 / 09 / 10 / 11 / 12. The notebook is a teaching artifact, not a test. Cell 14's anchor sanity check prints `OK` or `MISMATCH` rather than raising.

---

## What's In vs. What's Out

| In scope | Out of scope | Where it lands |
|---|---|---|
| Hybrid peer definition (`min_overlap` floor + `top_n_peers` cap) | Pure-threshold or pure-top-N peer pools | Possibly a Streamlit knob; not yet |
| Tunable `min_overlap`, `top_n_peers`, `threshold` | Per-peer weighting (e.g. demographic-similarity bonuses) | Strategy 4 calibration if needed |
| Combined-product score (`sum(overlap × peer_rating)`) | Cosine similarity / Pearson correlation / matrix factorization | Out of scope per [`CLAUDE.md`](../CLAUDE.md) — no ML fallbacks |
| Per-rec `via_peers` + `peer_chains` (≤ 3) | Top-3-strongest-chains ranked by score contribution (vs. by unwind order) | Possibly Strategy 4 |
| Overlap counted from shared ≥-threshold ratings | Overlap counted from any shared rating (incl. dislikes) | Out — collapses the "similar users also loved this" framing |
| Empty list on cold start | Demographic-pivot fallback for cold users | **Strategy 4** ([T-22]) — composite |
| `UNWIND`, `collect`, `reduce()`, list comprehensions, `head()`, `toString()`, `[..3]` slice | `apoc.*` helpers | Not needed |
| Read queries only | Write queries (`CREATE`, `MERGE`) | Notebooks 04 → 07 |
| Soft prints | Hard asserts / pytest | Out of project scope |
| Tie-break `(score DESC, title ASC)` | Popularity-weighted tie-breaks | Possibly Strategy 4 |

---

## Quick Sanity Check Before Running

If a cell errors on first run, it's almost always one of these:

1. **Notebooks 03 → 07 haven't been run against the current AuraDB instance.** Cell 2's peer profile returns zeros — no data is loaded. Re-run the load notebooks.
2. **AuraDB instance paused.** Free-tier instances auto-pause; resume from [console.neo4j.io](https://console.neo4j.io).
3. **`.env` missing or stale.** `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` must point to the live instance.
4. **User 196 not in dataset.** Same recurring anchor as notebooks 09 / 10 / 11 / 12 — if those work, this will too.
5. **`from recommender import collaborative_filtering, COLLABORATIVE_CYPHER` fails.** [`src/recommender.py`](../src/recommender.py) must use `from graph import run_query` (not `from src.graph import …`), matching the notebook's `sys.path` setup.
6. **Empty result at default knobs.** If `collaborative_filtering(user)` returns `[]` for a real user, the most likely cause is that no peer cleared the `min_overlap = 3` floor — i.e. the user is too thin for the default. That's the contract, not a bug. Drop `min_overlap` and re-run, or rely on Strategy 4's fallback (T-22).