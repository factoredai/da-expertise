# Unified Interface — `get_recommendations()`

The single entry point for callers (Streamlit, notebooks, ad-hoc scripts) to ask *"give me recommendations for user X using strategy Y."* Wraps the four strategies built in [T-19](11_strategy_genre_affinity.md), [T-20](12_strategy_director_actor.md), [T-21](13_strategy_collaborative_filtering.md), [T-22](14_strategy_composite_multi_signal.md). The wrapper does not change behavior — it dispatches to the existing strategy function by display name and forwards strategy-specific knobs verbatim.

Implementation: [`src/recommender.py`](../src/recommender.py) — `get_recommendations()`, just below the `STRATEGIES` dict.

---

## The Signature

```python
def get_recommendations(
    user_id: int,
    strategy: str,
    limit: int = 10,
    **kwargs,
) -> list[dict]:
```

- **`user_id`** — the MovieLens user to recommend for (e.g. `196`, the recurring anchor across notebooks 09-14).
- **`strategy`** — one of the four display names: `"Genre Affinity"`, `"Director / Actor Affinity"`, `"Collaborative Filtering"`, `"Composite Multi-Signal"`. These are the exact keys of `STRATEGIES`, which Streamlit also iterates for its dropdown.
- **`limit`** — number of recommendations to return. Forwarded as `k` to the underlying strategy. Default 10, matching each strategy's own default.
- **`**kwargs`** — strategy-specific knobs. Anything you'd pass to the underlying function (`threshold`, `top_n_genres`, `w_genre`, `min_overlap`, …) flows through unchanged. A kwarg the underlying strategy doesn't accept raises `TypeError` at call time — the typo surfaces immediately rather than silently producing wrong results.

Returns `list[dict]` — whatever the underlying strategy returned. The wrapper does not normalize the explainability shape (see decision below).

---

## Design Decisions

- **Display strings as the strategy key.** The wrapper accepts the same human-readable names already in `STRATEGIES`. One source of truth — the dict drives both the dispatch table and the Streamlit dropdown. No parallel slug system.
- **`**kwargs` pass-through.** Strategy-specific knobs flow through unchanged. Callers (or Streamlit sidebar widgets) can tune any underlying parameter without the wrapper having to know about it.
- **`TypeError` on unknown kwarg is intentional.** A typo like `top_n_genress=5` raises immediately rather than silently being ignored. Catches knob-name typos at the call site.
- **`ValueError` on unknown strategy.** If `strategy` isn't in `STRATEGIES`, the wrapper raises with both the bad name and the full list of valid keys — no need to open `recommender.py` to debug a typo. `ValueError` (bad input value) is the standard Python convention; `KeyError` (dict-internals failure) would leak the implementation detail.
- **Return-shape pass-through.** Each strategy already returns its own explainability shape (`matched_genres + seed_movies` / `via_people + seed_chains` / `via_peers + peer_chains` / `via_strategies + chains`). The wrapper does **not** normalize into a single `explanation: str` field — that would throw away the per-strategy detail that T-19/20/21/22 spent four tasks building. Streamlit branches on strategy when rendering anyway.
- **`limit=10` default.** Each underlying strategy defaults `k=10`; the wrapper matches for consistency.
- **`k` / `limit` collision lets Python raise.** If a caller passes both `limit=10` and `k=5`, Python raises `TypeError: got multiple values for keyword argument 'k'`. The native message is clear enough; no custom handling needed.
- **No companion notebook.** T-23 is a dispatcher, not a teaching artifact. The four strategies are demonstrated in notebooks 11/12/13/14. T-24 (Streamlit) is the real exercise of the unified interface.
- **Function position.** Lives immediately after the `STRATEGIES` dict in [`src/recommender.py`](../src/recommender.py). Reads top-to-bottom: four strategies → dispatch dict → unified entry point.
- **`STRATEGIES` stays public.** Streamlit needs it for the dropdown; no rename, no underscore-prefix.
- **Verification is a one-shot shell check.** No file artifact — load the module, call all four strategies through the wrapper for user 196, confirm each returns recs and the bad-strategy case raises `ValueError`.

---

## Usage Examples

Basic call — pass the display name:

```python
from recommender import get_recommendations

recs = get_recommendations(196, "Genre Affinity", limit=5)
# [{'movieId': 50, 'title': 'Star Wars (1977)', 'score': ..., 'matched_genres': [...], 'seed_movies': [...]}, ...]
```

Strategy 4 with a non-default weight, via `**kwargs`:

```python
recs = get_recommendations(196, "Composite Multi-Signal", limit=10, w_collab=3.0)
# Strategy-3 contributors get triple weight; the returned list skews toward collaborative signal.
```

Strategy-specific knob (any kwarg the underlying function accepts works):

```python
recs = get_recommendations(196, "Genre Affinity", limit=5, threshold=3.5)
# Lower-threshold pool; more seed ratings count toward affinity.
```

Bad strategy name — `ValueError` lists the valid keys:

```python
get_recommendations(196, "Genre Affinitee", limit=5)
# ValueError: Unknown strategy 'Genre Affinitee'. Valid: ['Genre Affinity',
# 'Director / Actor Affinity', 'Collaborative Filtering', 'Composite Multi-Signal']
```

Bad kwarg — Python's native `TypeError` surfaces the typo:

```python
get_recommendations(196, "Genre Affinity", limit=5, top_n_genress=3)
# TypeError: genre_affinity() got an unexpected keyword argument 'top_n_genress'
```

---

## What's In vs. What's Out

| In scope | Out of scope | Where it lands |
|---|---|---|
| Dispatch by display string | Slug aliases (`"genre"`, `"composite"`) | Out — one source of truth |
| `**kwargs` pass-through | Per-strategy parameter validation | Out — Python raises `TypeError` on its own |
| `ValueError` on unknown strategy | Silent empty-list return | Out — silent failures hide bugs |
| Pass-through return shape | Normalized `explanation: str` field | Streamlit branches on strategy |
| Public `STRATEGIES` dict | Underscore-prefixed private dict | Streamlit needs it for the dropdown |
| `limit=10` default | Required positional `limit` | Out — match underlying defaults |
| Native `TypeError` on `k` / `limit` collision | Custom guard with friendly message | Out — Python's message is clear enough |
| One-shot shell verification | Notebook test artifact | T-24 (Streamlit) is the real exercise |
| Five-line dispatcher | Caching / logging / async | T-24+ if ever |

---

## Quick Sanity Check Before Running

If `get_recommendations` errors on first use, it's almost always one of these:

1. **Notebooks 03 → 07 haven't been run against the current AuraDB instance.** No data is loaded; every strategy returns `[]`. Re-run the load notebooks.
2. **AuraDB instance paused.** Free-tier instances auto-pause; resume from [console.neo4j.io](https://console.neo4j.io).
3. **`.env` missing or stale.** `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` must point to the live instance.
4. **`from recommender import get_recommendations, STRATEGIES` fails.** [`src/recommender.py`](../src/recommender.py) must still use `from graph import run_query`, and `STRATEGIES` must still exist directly above the new function.
5. **`ValueError: Unknown strategy '...'`.** The strategy string must match a `STRATEGIES` key exactly (case-sensitive, spaces and slashes preserved). The error message itself lists the four valid keys — copy-paste from there.
6. **`TypeError: got an unexpected keyword argument '...'`.** A kwarg name doesn't match any parameter of the underlying strategy. Check the strategy's signature in [`src/recommender.py`](../src/recommender.py) for the exact spelling.
