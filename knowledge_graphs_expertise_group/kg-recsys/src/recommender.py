"""Recommendation strategies — Cypher-only.

Each strategy is one function returning list[dict]. Every result dict carries an
explainability payload (e.g. matched_genres + seed_movies for Strategy 1).
Empty list = no signal; the unified interface (Strategy 4) handles fallbacks.
"""

from graph import run_query


GENRE_AFFINITY_CYPHER = """
// Phase 1 — user's top genres by count of >= threshold ratings
MATCH (u:User {userId: $userId})-[r:RATED]->(:Movie)-[:IN_GENRE]->(g:Genre)
WHERE r.rating >= $threshold
WITH u, g, count(*) AS affinity
ORDER BY affinity DESC
LIMIT $top_n_genres
WITH u, collect({g: g, a: affinity}) AS scored_genres

// Phase 2 — global seeds: user's >= threshold titles in those top genres (up to 5)
UNWIND scored_genres AS sg
WITH u, scored_genres, sg.g AS top_g
MATCH (u)-[r2:RATED]->(seed:Movie)-[:IN_GENRE]->(top_g)
WHERE r2.rating >= $threshold
WITH u, scored_genres, collect(DISTINCT seed.title)[..5] AS seed_movies

// Phase 3 — unseen recs in top genres, scored + ranked
UNWIND scored_genres AS sg
WITH u, seed_movies, sg.g AS top_g, sg.a AS top_a
MATCH (top_g)<-[:IN_GENRE]-(rec:Movie)
WHERE NOT EXISTS { (u)-[:RATED]->(rec) }
WITH rec, seed_movies,
     sum(top_a) AS score,
     collect(DISTINCT top_g.name) AS matched_genres
RETURN rec.movieId AS movieId,
       rec.title AS title,
       rec.year AS year,
       score,
       matched_genres,
       seed_movies
ORDER BY score DESC, title ASC
LIMIT $k
"""


def genre_affinity(
    user_id: int,
    k: int = 10,
    top_n_genres: int = 3,
    threshold: float = 4.0,
) -> list[dict]:
    """Strategy 1 — Genre affinity (single-hop).

    Returns up to k unseen movies in the user's top n genres (ranked by count of
    their >= threshold ratings in each genre). Each rec carries:
        - movieId, title, year
        - score: sum of affinity counts across matched top genres
        - matched_genres: list[str] — which of the user's top genres the rec is in
        - seed_movies: list[str] — up to 5 of the user's >= threshold titles in those genres

    Empty list = user has no ratings >= threshold (or no such user). Callers
    handle this as "no signal" (Strategy 4 / composite is responsible for fallback).
    """
    return run_query(
        GENRE_AFFINITY_CYPHER,
        {
            "userId": user_id,
            "k": k,
            "top_n_genres": top_n_genres,
            "threshold": threshold,
        },
    )


DIRECTOR_ACTOR_CYPHER = """
// Phase 1a — user's top directors by count of >= threshold ratings
MATCH (u:User {userId: $userId})-[r1:RATED]->(seed_d:Movie)-[:DIRECTED_BY]->(d:Director)
WHERE r1.rating >= $threshold
WITH u, d, count(seed_d) AS affinity, collect(DISTINCT seed_d.title) AS seed_titles
ORDER BY affinity DESC
LIMIT $top_n_directors
WITH u, collect({
  person_id: elementId(d),
  name: d.name,
  kind: 'director',
  affinity: affinity,
  seeds: seed_titles
}) AS top_dirs

// Phase 1b — user's top top-billed actors
MATCH (u)-[r2:RATED]->(seed_a:Movie)-[fa:FEATURES_ACTOR]->(a:Actor)
WHERE r2.rating >= $threshold AND fa.billing_order <= $max_billing
WITH u, top_dirs, a, count(seed_a) AS affinity, collect(DISTINCT seed_a.title) AS seed_titles
ORDER BY affinity DESC
LIMIT $top_n_actors
WITH u, top_dirs, collect({
  person_id: elementId(a),
  name: a.name,
  kind: 'actor',
  affinity: affinity,
  seeds: seed_titles
}) AS top_actors
WITH u, top_dirs + top_actors AS top_people

// Phase 3 — walk forward to unseen recs via either route, score, rank
UNWIND top_people AS tp
MATCH (rec:Movie)
WHERE NOT EXISTS { (u)-[:RATED]->(rec) }
  AND (
    (tp.kind = 'director' AND EXISTS {
      MATCH (rec)-[:DIRECTED_BY]->(d2:Director)
      WHERE elementId(d2) = tp.person_id
    })
    OR
    (tp.kind = 'actor' AND EXISTS {
      MATCH (rec)-[fa2:FEATURES_ACTOR]->(a2:Actor)
      WHERE elementId(a2) = tp.person_id AND fa2.billing_order <= $max_billing
    })
  )
WITH rec, collect(tp) AS connecting_people
WITH rec,
     [p IN connecting_people | p.name + ' (' + p.kind + ')'] AS via_people,
     reduce(s = 0, p IN connecting_people | s + p.affinity) AS score,
     [p IN connecting_people | head(p.seeds) + ' → ' + p.name + ' (' + p.kind + ') → ' + rec.title][..3] AS seed_chains
RETURN rec.movieId AS movieId,
       rec.title   AS title,
       rec.year    AS year,
       score,
       via_people,
       seed_chains
ORDER BY score DESC, title ASC
LIMIT $k
"""


def director_actor_affinity(
    user_id: int,
    k: int = 10,
    top_n_directors: int = 3,
    top_n_actors: int = 5,
    max_billing: int = 5,
    threshold: float = 4.0,
) -> list[dict]:
    """Strategy 2 — Director/Actor affinity (multi-hop).

    Returns up to k unseen movies connected to the user via either:
      - a top director (ranked by count of user's >= threshold ratings of their films), or
      - a top top-billed actor (billing_order <= max_billing).

    Each rec carries:
        - movieId, title, year
        - score: sum of affinity counts across matched top people
        - via_people: list[str] — names + kinds of top people connecting the user to this rec
        - seed_chains: list[str] — up to 3 "<seed> → <person> (<kind>) → <rec>" paths

    Empty list = user has no ratings >= threshold connecting to any director/actor
    (or no such user). Strategy 4 / composite owns the fallback.
    """
    return run_query(
        DIRECTOR_ACTOR_CYPHER,
        {
            "userId": user_id,
            "k": k,
            "top_n_directors": top_n_directors,
            "top_n_actors": top_n_actors,
            "max_billing": max_billing,
            "threshold": threshold,
        },
    )


COLLABORATIVE_CYPHER = """
// Phase 1 — find peers: users sharing >= min_overlap >=-threshold-rated movies
MATCH (u:User {userId: $userId})-[r1:RATED]->(seed:Movie)<-[r2:RATED]-(peer:User)
WHERE r1.rating >= $threshold
  AND r2.rating >= $threshold
  AND peer <> u
WITH u, peer, count(DISTINCT seed) AS overlap, collect(DISTINCT seed.title) AS shared_titles
WHERE overlap >= $min_overlap
WITH u, peer, overlap, shared_titles
ORDER BY overlap DESC
LIMIT $top_n_peers
WITH u, collect({
  peer_id: peer.userId,
  overlap: overlap,
  shared: shared_titles
}) AS top_peers

// Phase 2 — for each top peer, find their >=-threshold-rated movies the user hasn't seen
UNWIND top_peers AS tp
MATCH (peer:User {userId: tp.peer_id})-[r3:RATED]->(rec:Movie)
WHERE r3.rating >= $threshold
  AND NOT EXISTS { (u)-[:RATED]->(rec) }
WITH rec, tp, r3.rating AS peer_rating

// Phase 3 — group by rec, score with combined product, build explainability
WITH rec, collect({
  peer_id: tp.peer_id,
  overlap: tp.overlap,
  peer_rating: peer_rating,
  shared: tp.shared
}) AS contributing
WITH rec,
     reduce(s = 0.0, c IN contributing | s + (c.overlap * c.peer_rating)) AS score,
     [c IN contributing | {peer_id: c.peer_id, overlap: c.overlap}] AS via_peers,
     [c IN contributing | head(c.shared) + ' → peer ' + toString(c.peer_id) + ' → ' + rec.title][..3] AS peer_chains
RETURN rec.movieId AS movieId,
       rec.title   AS title,
       rec.year    AS year,
       score,
       via_peers,
       peer_chains
ORDER BY score DESC, title ASC
LIMIT $k
"""


def collaborative_filtering(
    user_id: int,
    k: int = 10,
    min_overlap: int = 3,
    top_n_peers: int = 25,
    threshold: float = 4.0,
) -> list[dict]:
    """Strategy 3 — Collaborative filtering via shared graph neighborhood.

    Finds peer users who share >= min_overlap >=-threshold-rated movies with the
    user, takes the top top_n_peers by overlap count, then recommends the peers'
    other >=-threshold-rated movies the user hasn't seen.

    Each rec carries:
        - movieId, title, year
        - score: sum of (peer.overlap * peer.rating_of_rec) across all contributing peers
        - via_peers: list[dict] — [{peer_id, overlap}, ...] for every peer who voted for this rec
        - peer_chains: list[str] — up to 3 "<shared_title> → peer <id> → <rec>" paths

    Empty list = user has no ratings >= threshold connecting to any peer at the
    min_overlap floor (or no such user). Strategy 4 / composite owns the fallback.
    """
    return run_query(
        COLLABORATIVE_CYPHER,
        {
            "userId": user_id,
            "k": k,
            "min_overlap": min_overlap,
            "top_n_peers": top_n_peers,
            "threshold": threshold,
        },
    )


COMPOSITE_CYPHER = f"""
// Subquery 1 — Strategy 1: genre affinity, top $inner_k
CALL {{
{GENRE_AFFINITY_CYPHER.replace("$k", "$inner_k").strip()}
}}
WITH collect({{
  movieId: movieId, title: title, year: year,
  chain: head(matched_genres) + ' → ' + head(seed_movies) + ' → ' + title
}}) AS genre_list
UNWIND range(0, size(genre_list) - 1) AS i
WITH genre_list, i
WITH collect({{
  movieId: genre_list[i].movieId,
  title: genre_list[i].title,
  year: genre_list[i].year,
  strategy: 'genre',
  rank: i + 1,
  chain: genre_list[i].chain
}}) AS genre_ranked

// Subquery 2 — Strategy 2: director/actor affinity, top $inner_k
CALL {{
{DIRECTOR_ACTOR_CYPHER.replace("$k", "$inner_k").strip()}
}}
WITH genre_ranked, collect({{
  movieId: movieId, title: title, year: year,
  chain: head(seed_chains)
}}) AS da_list
UNWIND range(0, size(da_list) - 1) AS j
WITH genre_ranked, da_list, j
WITH genre_ranked, collect({{
  movieId: da_list[j].movieId,
  title: da_list[j].title,
  year: da_list[j].year,
  strategy: 'director_actor',
  rank: j + 1,
  chain: da_list[j].chain
}}) AS da_ranked

// Subquery 3 — Strategy 3: collaborative filtering, top $inner_k
CALL {{
{COLLABORATIVE_CYPHER.replace("$k", "$inner_k").strip()}
}}
WITH genre_ranked, da_ranked, collect({{
  movieId: movieId, title: title, year: year,
  chain: head(peer_chains)
}}) AS cf_list
UNWIND range(0, size(cf_list) - 1) AS m
WITH genre_ranked, da_ranked, cf_list, m
WITH genre_ranked, da_ranked, collect({{
  movieId: cf_list[m].movieId,
  title: cf_list[m].title,
  year: cf_list[m].year,
  strategy: 'collaborative',
  rank: m + 1,
  chain: cf_list[m].chain
}}) AS cf_ranked

// Merge: union three rank-lists, group by movieId, weighted RRF score
WITH genre_ranked + da_ranked + cf_ranked AS all_results
UNWIND all_results AS r
WITH r.movieId AS movieId, r.title AS title, r.year AS year,
     collect({{strategy: r.strategy, rank: r.rank, chain: r.chain}}) AS contributions
WITH movieId, title, year, contributions,
     reduce(s = 0.0, c IN contributions |
       s + CASE c.strategy
             WHEN 'genre'          THEN $w_genre          / toFloat(c.rank)
             WHEN 'director_actor' THEN $w_director_actor / toFloat(c.rank)
             WHEN 'collaborative'  THEN $w_collab         / toFloat(c.rank)
           END
     ) AS score,
     [c IN contributions | c.strategy] AS via_strategies,
     [c IN contributions | c.chain]    AS chains
RETURN movieId, title, year, score, via_strategies, chains
ORDER BY score DESC, title ASC
LIMIT $k
"""


def composite_multi_signal(
    user_id: int,
    k: int = 10,
    inner_k: int = 15,
    w_genre: float = 1.0,
    w_director_actor: float = 1.0,
    w_collab: float = 1.0,
    threshold: float = 4.0,
    top_n_genres: int = 3,
    top_n_directors: int = 3,
    top_n_actors: int = 5,
    max_billing: int = 5,
    min_overlap: int = 3,
    top_n_peers: int = 25,
) -> list[dict]:
    """Strategy 4 — Composite multi-signal via weighted Reciprocal Rank Fusion.

    Runs the three sub-strategies (genre affinity, director/actor affinity,
    collaborative filtering) as CALL subqueries in a single Cypher round-trip,
    each fetching its top inner_k recs. Each rec gets a weighted RRF score:

        score = sum_over_contributing_strategies(w_s / rank_s)

    where rank_s is the rec's 1-indexed position in strategy s's ranked list.

    Each rec carries:
        - movieId, title, year
        - score: weighted sum of 1/rank across contributing strategies
        - via_strategies: list[str] — which of {'genre', 'director_actor',
          'collaborative'} surfaced this rec
        - chains: list[str] — one chain per contributing strategy, same order
          as via_strategies

    Empty list = all three sub-strategies returned empty (cold start at the
    composite level). Cold-start fallback (demographic pivot) is out of scope
    for T-22; filed as T-22b.
    """
    return run_query(
        COMPOSITE_CYPHER,
        {
            "userId": user_id,
            "k": k,
            "inner_k": inner_k,
            "w_genre": w_genre,
            "w_director_actor": w_director_actor,
            "w_collab": w_collab,
            "threshold": threshold,
            "top_n_genres": top_n_genres,
            "top_n_directors": top_n_directors,
            "top_n_actors": top_n_actors,
            "max_billing": max_billing,
            "min_overlap": min_overlap,
            "top_n_peers": top_n_peers,
        },
    )


STRATEGIES = {
    "Genre Affinity": genre_affinity,
    "Director / Actor Affinity": director_actor_affinity,
    "Collaborative Filtering": collaborative_filtering,
    "Composite Multi-Signal": composite_multi_signal,
}


def get_recommendations(
    user_id: int,
    strategy: str,
    limit: int = 10,
    **kwargs,
) -> list[dict]:
    """Unified entry point — dispatch to one of the four recommendation strategies.

    Parameters
    ----------
    user_id : int
        The MovieLens user to recommend for.
    strategy : str
        One of the display names in ``STRATEGIES``:
        ``"Genre Affinity"``, ``"Director / Actor Affinity"``,
        ``"Collaborative Filtering"``, ``"Composite Multi-Signal"``.
    limit : int, default 10
        Maximum number of recommendations to return. Forwarded as ``k`` to the
        underlying strategy function.
    **kwargs
        Strategy-specific knobs (e.g. ``threshold``, ``top_n_genres``,
        ``w_genre``, ``min_overlap``). Forwarded verbatim. If you pass a kwarg
        the underlying strategy doesn't accept, Python raises ``TypeError`` at
        call time — useful for catching knob-name typos.

    Returns
    -------
    list[dict]
        Whatever the underlying strategy returns. Each strategy has its own
        explainability shape — see the four strategy functions for the exact
        keys. The wrapper does not normalize.

    Raises
    ------
    ValueError
        If ``strategy`` is not one of the four supported display names.

    Examples
    --------
    >>> get_recommendations(196, "Genre Affinity", limit=5)
    [{'movieId': ..., 'title': ..., 'score': ..., 'matched_genres': [...], ...}, ...]

    >>> get_recommendations(196, "Composite Multi-Signal", limit=10, w_collab=3.0)
    [{'movieId': ..., 'title': ..., 'score': ..., 'via_strategies': [...], ...}, ...]

    >>> get_recommendations(196, "Genre Affinity", limit=5, threshold=3.5)
    [...]  # same shape, lower-threshold pool

    >>> get_recommendations(196, "Genre Affinitee", limit=5)
    Traceback (most recent call last):
        ...
    ValueError: Unknown strategy 'Genre Affinitee'. Valid: ['Genre Affinity', ...]
    """
    if strategy not in STRATEGIES:
        raise ValueError(
            f"Unknown strategy '{strategy}'. "
            f"Valid: {list(STRATEGIES.keys())}"
        )
    return STRATEGIES[strategy](user_id, k=limit, **kwargs)
