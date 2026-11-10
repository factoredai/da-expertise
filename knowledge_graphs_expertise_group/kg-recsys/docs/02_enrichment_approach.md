# Data Enrichment Approach

How we enrich the base MovieLens 100K dataset with TMDB metadata (actors, directors, genres) to build the Knowledge Graph.

---

## The Problem

MovieLens and TMDB use different internal IDs — there is no direct key to join on. The only bridge between the two datasets is the **movie title + release year**, which MovieLens stores in the format `"Toy Story (1995)"`.

Note: MovieLens `u.item` includes IMDB URLs, but these are old search-style links (`title-exact?Toy%20Story%20(1995)`) — they do not contain extractable IMDB IDs, so the TMDB `/find` endpoint cannot be used.

---

## Pipeline

```
u.item (MovieLens)
   ↓
Parse title + year
   ↓
Automated TMDB search (title + year)
   ↓
   ├── Matched → enriched_movies.csv
   └── Unmatched
           ↓
       Retry without year (title only)
           ↓
           ├── Recovered → enriched_movies.csv
           └── Still unmatched → failed_matches.csv
                                       ↓
                              Manual lookup in TMDB browser
                                       ↓
                          Inline mapping dict in notebook
                          (movieId → tmdb_id)
                                       ↓
                          Re-run enrichment using manual IDs
                                       ↓
                              enriched_movies.csv (complete)
```

**Final result: 1679 / 1682 matched (99.8%)**

---

## Step 1 — Automated TMDB Search

For each movie in `u.item`:
1. Parse the title and year from the MovieLens format (e.g. `"Toy Story (1995)"` → title: `Toy Story`, year: `1995`)
2. Search TMDB using title + year
3. If a result is returned → fetch credits (actors, directors) and store
4. If no result → move to retry step

**Known edge cases in MovieLens titles:**
- Inverted articles: `"Silence of the Lambs, The (1991)"` → cleaned to `"The Silence of the Lambs"` before searching
- Missing year: some titles have no year in parentheses — search is run without year
- Non-English titles: may not match TMDB search reliably

---

## Step 2 — Retry Without Year

Many failures are caused by a **year mismatch** between MovieLens (which uses home video or international release year) and TMDB (which uses theatrical release date). A one-year offset is common.

For each unmatched movie, a second search is run using **title only** (year dropped):
- If a result is returned → fetch credits and store as matched
- If still no result → flag as failed

This step recovered **62 of the 78 initial failures**.

---

## Step 3 — Failed Matches

Movies that failed both search attempts are saved to `data/enriched/failed_matches.csv`:

| Column | Description |
|---|---|
| `movieId` | MovieLens internal ID |
| `raw_title` | Original title string from `u.item` |
| `parsed_title` | Title after parsing (articles cleaned) |
| `parsed_year` | Year extracted from title |

This file is **not committed** to the repo — it is auto-generated each run.

---

## Step 4 — Manual Mapping

For movies that failed both search attempts, look them up manually at [themoviedb.org](https://www.themoviedb.org) and record their TMDB IDs directly in the notebook as an inline Python list:

```python
manual_mapping = [
    {"movieId": 6,   "tmdb_id": 37557},
    {"movieId": 912, "tmdb_id": 11808},
    # ...
]
```

The `tmdb_id` is the number in the TMDB URL: `themoviedb.org/movie/`**`862`**`-toy-story` → `862`.

> Note: some MovieLens entries are TV miniseries classified under `/tv/` on TMDB. These cannot be matched with the movie endpoint and are accepted as permanent gaps.

---

## Step 5 — Re-run with Manual IDs

For each entry in `manual_mapping`, the enrichment fetches metadata directly using the `tmdb_id` — skipping the search step. The `/movie/{tmdb_id}` endpoint is used (returns full genre objects instead of `genre_ids`).

---

## Output

All enriched data lands in `data/enriched/` (gitignored):

| File | Content |
|---|---|
| `enriched_movies.csv` | Full enriched dataset (automated + retry + manual matches) |
| `failed_matches.csv` | Movies with no match after all steps |

---

## What We Extract from TMDB

| Field | Column in CSV | Used for |
|---|---|---|
| Top 10 cast members (by billing order) | `cast` | `FEATURES_ACTOR` relationships |
| Director(s) | `directors` | `DIRECTED_BY` relationships |
| Genre IDs | `genre_ids` | `IN_GENRE` relationships |
| Genre names | `genre_names` | Human-readable labels — no lookup table needed |

Cast is ordered by **billing order** (how actors appear in the official movie credits), so the top 10 are reliably the main cast.
