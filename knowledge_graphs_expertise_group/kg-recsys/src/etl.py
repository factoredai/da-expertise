"""File readers for MovieLens 100K + TMDB-enriched data.

This module is a thin library of pure file-readers. It does NOT touch Neo4j
directly — the load orchestration (and the inline Cypher MERGE statements) live
in notebooks/04_load_nodes.ipynb. That split keeps the pedagogically interesting
graph code visible in the notebook while the boring CSV parsing stays here.

TMDB enrichment itself was done as a one-shot in notebooks/02_tmdb_enrichment.ipynb;
its output is data/enriched/enriched_movies.csv. This module reads that file but
never calls the API.
"""

import ast
import re
from pathlib import Path

import pandas as pd

# Resolve paths from this file's location so readers work regardless of CWD
# (notebook CWD is notebooks/, scripts may run from repo root).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = _PROJECT_ROOT / "data" / "raw" / "ml-100k"
ENRICHED_DIR = _PROJECT_ROOT / "data" / "enriched"

# Matches the trailing " (YYYY)" on ml-100k titles, e.g. "Toy Story (1995)".
_TITLE_YEAR_RE = re.compile(r"^(.*?)\s*\((\d{4})\)\s*$")


# ---------------------------------------------------------------------------
# Readers — one per node label in T-10's scope
# ---------------------------------------------------------------------------

def read_genres() -> list[str]:
    """The 19 ml-100k genre names from u.genre, in file order."""
    names = []
    with open(RAW_DIR / "u.genre", "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            name, _ = line.split("|")
            names.append(name)
    return names


def read_users() -> pd.DataFrame:
    """u.user → DataFrame[userId, age]. Drops gender/occupation/zip for T-10 strict scope."""
    cols = ["userId", "age", "gender", "occupation", "zip"]
    df = pd.read_csv(
        RAW_DIR / "u.user",
        sep="|",
        names=cols,
        encoding="latin-1",
    )
    return df[["userId", "age"]]


def read_movies() -> pd.DataFrame:
    """u.item left-joined with enriched_movies.csv → DataFrame[movieId, title, year, tmdbId].

    title is year-stripped ("Toy Story (1995)" → "Toy Story"); year comes from
    the same suffix via regex. tmdbId is None for the ~1% of movies TMDB
    couldn't match — those rows still produce a Movie node, just without tmdbId.
    """
    item_cols = (
        ["movieId", "title_raw", "release_date", "video_release", "imdb_url"]
        + [f"genre_{i}" for i in range(19)]
    )
    items = pd.read_csv(
        RAW_DIR / "u.item",
        sep="|",
        names=item_cols,
        encoding="latin-1",
    )
    items["title"] = items["title_raw"].apply(_clean_title)
    items["year"] = items["title_raw"].apply(_extract_year)

    enriched = pd.read_csv(ENRICHED_DIR / "enriched_movies.csv")
    enriched = enriched[["movieId", "tmdb_id"]].rename(columns={"tmdb_id": "tmdbId"})

    df = items[["movieId", "title", "year"]].merge(enriched, on="movieId", how="left")
    df["tmdbId"] = df["tmdbId"].astype("Int64")
    return df


def read_directors() -> list[str]:
    """Flatten + dedupe the `directors` column from enriched_movies.csv."""
    return _read_unique_names(column="directors")


def read_actors() -> list[str]:
    """Flatten + dedupe the `cast` column from enriched_movies.csv (top-10 per movie)."""
    return _read_unique_names(column="cast")


def read_occupations() -> list[str]:
    """The 21 ml-100k occupation names from u.occupation, in file order."""
    names = []
    with open(RAW_DIR / "u.occupation", "r") as f:
        for line in f:
            line = line.strip()
            if line:
                names.append(line)
    return names


def read_genders() -> list[str]:
    """The two raw gender codes used by u.user. Kept as 'M'/'F' for source fidelity."""
    return ["M", "F"]


# ---------------------------------------------------------------------------
# Edge readers
#
# These return flat DataFrames where every row represents one future edge.
# Python's job is the explode/melt; Cypher's job is then a clean
# MATCH (a) MATCH (b) MERGE (a)-[:R]->(b).
# ---------------------------------------------------------------------------

def read_ratings() -> pd.DataFrame:
    """u.data → DataFrame[userId, movieId, rating, timestamp]. 100,000 rows.

    rating is cast to float to match the schema contract (ml-100k stores ints,
    later MovieLens variants use 0.5-step floats). timestamp is Unix epoch int.
    """
    df = pd.read_csv(
        RAW_DIR / "u.data",
        sep="\t",
        names=["userId", "movieId", "rating", "timestamp"],
    )
    df["rating"] = df["rating"].astype(float)
    return df


def read_movie_genres() -> pd.DataFrame:
    """u.item → DataFrame[movieId, genre]. One row per movie-genre membership.

    u.item has 19 boolean columns (one per ml-100k genre, in u.genre file order).
    This melts them to long form and keeps only rows where the bit is 1.
    """
    genre_names = read_genres()
    item_cols = (
        ["movieId", "title_raw", "release_date", "video_release", "imdb_url"]
        + [f"genre_{i}" for i in range(19)]
    )
    items = pd.read_csv(
        RAW_DIR / "u.item",
        sep="|",
        names=item_cols,
        encoding="latin-1",
    )
    rename_map = {f"genre_{i}": name for i, name in enumerate(genre_names)}
    items = items.rename(columns=rename_map)
    melted = items.melt(
        id_vars=["movieId"],
        value_vars=genre_names,
        var_name="genre",
        value_name="present",
    )
    return melted[melted["present"] == 1][["movieId", "genre"]].reset_index(drop=True)


def read_movie_directors() -> pd.DataFrame:
    """enriched_movies.csv → DataFrame[movieId, name]. One row per movie-director edge.

    Skips unmatched movies (directors is NaN) and empty director lists.
    """
    return _explode_movie_names(column="directors")


def read_movie_cast() -> pd.DataFrame:
    """enriched_movies.csv → DataFrame[movieId, name, billing_order]. ≤10 rows per movie.

    billing_order is 1-based (1 = top billing) and comes from the list order in
    the cast column, which TMDB already returns sorted by billing. Skips
    unmatched movies and empty cast lists.
    """
    enriched = pd.read_csv(ENRICHED_DIR / "enriched_movies.csv")
    rows = []
    for _, row in enriched[["movieId", "cast"]].iterrows():
        cell = row["cast"]
        if pd.isna(cell):
            continue
        names = ast.literal_eval(cell)
        for billing_order, name in enumerate(names, start=1):
            rows.append({
                "movieId": int(row["movieId"]),
                "name": name,
                "billing_order": billing_order,
            })
    return pd.DataFrame(rows)


def read_user_occupation() -> pd.DataFrame:
    """u.user → DataFrame[userId, occupation]. 943 rows, one per user."""
    cols = ["userId", "age", "gender", "occupation", "zip"]
    df = pd.read_csv(RAW_DIR / "u.user", sep="|", names=cols, encoding="latin-1")
    return df[["userId", "occupation"]]


def read_user_gender() -> pd.DataFrame:
    """u.user → DataFrame[userId, gender]. 943 rows. Gender stays raw ('M' or 'F')."""
    cols = ["userId", "age", "gender", "occupation", "zip"]
    df = pd.read_csv(RAW_DIR / "u.user", sep="|", names=cols, encoding="latin-1")
    return df[["userId", "gender"]]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def to_records(df: pd.DataFrame) -> list[dict]:
    """DataFrame → list[dict] with NaN/pd.NA replaced by Python None.

    The Neo4j driver expects None for null values; pandas NaN does not survive
    serialization cleanly.
    """
    return [
        {k: (None if pd.isna(v) else v) for k, v in row.items()}
        for row in df.to_dict("records")
    ]


def _clean_title(title_with_year: str) -> str:
    m = _TITLE_YEAR_RE.match(title_with_year)
    return m.group(1) if m else title_with_year


def _extract_year(title_with_year: str) -> int | None:
    m = _TITLE_YEAR_RE.match(title_with_year)
    return int(m.group(2)) if m else None


def _read_unique_names(column: str) -> list[str]:
    enriched = pd.read_csv(ENRICHED_DIR / "enriched_movies.csv")
    series = enriched[column].dropna()
    seen: set[str] = set()
    for cell in series:
        for name in ast.literal_eval(cell):
            seen.add(name)
    return sorted(seen)


def _explode_movie_names(column: str) -> pd.DataFrame:
    """Explode a list-valued column from enriched_movies.csv into (movieId, name) edge rows.

    Skips NaN cells (movies TMDB couldn't match) and empty lists.
    """
    enriched = pd.read_csv(ENRICHED_DIR / "enriched_movies.csv")
    rows = []
    for _, row in enriched[["movieId", column]].iterrows():
        cell = row[column]
        if pd.isna(cell):
            continue
        for name in ast.literal_eval(cell):
            rows.append({"movieId": int(row["movieId"]), "name": name})
    return pd.DataFrame(rows)
