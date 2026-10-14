"""Streamlit interactive demo — 3 screens."""

import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components
import sys
import tempfile
from pathlib import Path

from neo4j.exceptions import AuthError, Neo4jError, ServiceUnavailable

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph import run_query
from recommender import STRATEGIES, get_recommendations

st.set_page_config(page_title="KG RecSys Demo", layout="wide")


def safe_run_query(query: str, params: dict | None = None) -> list[dict]:
    """Wrap `run_query` with user-friendly Streamlit error handling.

    Catches the three Neo4j error classes we expect at the screen layer:
      * ServiceUnavailable — AuraDB paused, network down, wrong URI
      * AuthError — bad credentials in `.env`
      * Neo4jError — generic query/server error (syntax, timeout, etc.)

    Renders `st.error` with an actionable next step and calls `st.stop()` so the
    current rerun ends cleanly instead of showing a half-drawn UI plus a red
    traceback. Subsequent reruns retry.
    """
    try:
        return run_query(query, params or {})
    except ServiceUnavailable:
        st.error(
            "Cannot reach Neo4j AuraDB. The instance may be paused or your "
            "network is offline. Resume from [console.neo4j.io](https://console.neo4j.io), "
            "then use **Clear all caches** in the sidebar and rerun."
        )
        st.stop()
    except AuthError:
        st.error(
            "Authentication to AuraDB failed. Check `NEO4J_USERNAME` / "
            "`NEO4J_PASSWORD` in your `.env`, then restart `streamlit run`."
        )
        st.stop()
    except Neo4jError as exc:
        st.error(
            f"Neo4j query error: {exc.message}. "
            "If you recently edited Cypher in a fetcher, clear caches and try again."
        )
        st.stop()


# ---------------------------------------------------------------------------
# Sidebar — title, navigation, per-screen caption, utilities
# ---------------------------------------------------------------------------

SCREENS = ["User Profile", "Recommendation Engine", "Graph Explorer"]
_SCREEN_CAPTIONS = {
    "User Profile":          "Ratings table + depth-1 KG neighborhood.",
    "Recommendation Engine": "Run any of the 4 strategies with full explainability.",
    "Graph Explorer":        "Search any movie or actor → render local subgraph.",
}

st.sidebar.markdown("## KG RecSys Demo")
st.sidebar.caption("MovieLens 100K · Neo4j AuraDB · Cypher-only logic")
st.sidebar.markdown("---")

screen = st.sidebar.radio("Navigate", SCREENS)
st.sidebar.caption(_SCREEN_CAPTIONS[screen])

st.sidebar.markdown("---")
if st.sidebar.button("Clear all caches", help="Drop every @st.cache_data result. Use after re-running a loader notebook."):
    st.cache_data.clear()
    st.rerun()


# ---------------------------------------------------------------------------
# Screen 1 — User Profile
# ---------------------------------------------------------------------------

# Color palette for the neighborhood subgraph — one color per node type so the
# schema is readable at a glance.
_NODE_COLORS = {
    "User":       "#4F8BF9",
    "Movie":      "#F4B400",
    "Occupation": "#0F9D58",
    "Gender":     "#DB4437",
    "Genre":      "#00B8D9",
    "Director":   "#FF6D00",
    "Actor":      "#8E24AA",
}


@st.cache_data(ttl=600)
def _fetch_ratings(uid: int) -> list[dict]:
    """User's rating history with year + top-3 genres per movie."""
    return safe_run_query(
        """
        MATCH (u:User {userId: $uid})-[r:RATED]->(m:Movie)
        OPTIONAL MATCH (m)-[:IN_GENRE]->(g:Genre)
        WITH m, r, collect(DISTINCT g.name)[..3] AS top_genres
        RETURN m.title  AS title,
               m.year   AS year,
               r.rating AS rating,
               top_genres AS genres
        ORDER BY r.rating DESC, m.title ASC
        """,
        {"uid": uid},
    )


@st.cache_data(ttl=600)
def _fetch_neighborhood(uid: int, top_n: int = 15) -> dict:
    """Depth-1 KG neighborhood: occupation, gender, top-N rated movies."""
    rows = safe_run_query(
        """
        MATCH (u:User {userId: $uid})
        OPTIONAL MATCH (u)-[:HAS_OCCUPATION]->(occ:Occupation)
        OPTIONAL MATCH (u)-[:HAS_GENDER]->(gen:Gender)
        OPTIONAL MATCH (u)-[r:RATED]->(m:Movie)
        WITH u, occ, gen, m, r
        ORDER BY r.rating DESC, m.title ASC
        WITH u, occ, gen,
             [x IN collect({mid: m.movieId, title: m.title, rating: r.rating})
              WHERE x.mid IS NOT NULL][..$top_n] AS top_movies
        RETURN u.userId       AS userId,
               occ.name       AS occupation,
               gen.name       AS gender,
               top_movies     AS top_movies
        """,
        {"uid": uid, "top_n": top_n},
    )
    return rows[0] if rows else {"userId": None, "occupation": None, "gender": None, "top_movies": []}


def _render_neighborhood(bundle: dict) -> str:
    """Build a pyvis Network from the neighborhood bundle, return HTML."""
    net = Network(height="500px", width="100%", bgcolor="#0e1117", font_color="white")
    net.toggle_physics(True)

    uid = bundle["userId"]
    user_node = f"u_{uid}"
    net.add_node(user_node, label=f"User {uid}", color=_NODE_COLORS["User"], size=28, shape="dot")

    if bundle.get("occupation"):
        occ_node = f"occ_{bundle['occupation']}"
        net.add_node(occ_node, label=bundle["occupation"], color=_NODE_COLORS["Occupation"], size=18, shape="dot")
        net.add_edge(user_node, occ_node, label="HAS_OCCUPATION", color="#888888")

    if bundle.get("gender"):
        gen_node = f"gen_{bundle['gender']}"
        net.add_node(gen_node, label=bundle["gender"], color=_NODE_COLORS["Gender"], size=18, shape="dot")
        net.add_edge(user_node, gen_node, label="HAS_GENDER", color="#888888")

    for movie in bundle.get("top_movies", []):
        mid = movie["mid"]
        movie_node = f"m_{mid}"
        net.add_node(
            movie_node,
            label=movie["title"],
            title=f"{movie['title']} — rated {movie['rating']}",
            color=_NODE_COLORS["Movie"],
            size=16,
            shape="dot",
        )
        net.add_edge(user_node, movie_node, label=f"RATED {movie['rating']}", color="#888888")

    tmp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html", encoding="utf-8")
    net.write_html(tmp.name, notebook=False, open_browser=False)
    with open(tmp.name, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Screen 2 helpers — must live above the if/elif chain (Python disallows defs
# between if and elif).
# ---------------------------------------------------------------------------

@st.cache_data(ttl=600)
def _fetch_recommendations(uid: int, strategy: str, limit: int) -> list[dict]:
    """Cached dispatch to the unified recommender interface."""
    return get_recommendations(uid, strategy, limit=limit)


def _render_explanation(strategy: str, rec: dict) -> None:
    """Render the strategy-specific explainability path inside the current container."""
    if strategy == "Genre Affinity":
        genres = ", ".join(rec.get("matched_genres") or [])
        seeds = ", ".join(rec.get("seed_movies") or [])
        if genres:
            st.markdown(f"**Matched on genres:** {genres}")
        if seeds:
            st.markdown(f"**Because you rated:** {seeds}")

    elif strategy == "Director / Actor Affinity":
        people = ", ".join(rec.get("via_people") or [])
        if people:
            st.markdown(f"**Via:** {people}")
        for chain in rec.get("seed_chains") or []:
            st.markdown(f"- {chain}")

    elif strategy == "Collaborative Filtering":
        peers = rec.get("via_peers") or []
        peer_summary = ", ".join(
            f"peer {p['peer_id']} (overlap {p['overlap']})" for p in peers
        )
        if peer_summary:
            st.markdown(f"**Via peers:** {peer_summary}")
        for chain in rec.get("peer_chains") or []:
            st.markdown(f"- {chain}")

    elif strategy == "Composite Multi-Signal":
        via = ", ".join(rec.get("via_strategies") or [])
        if via:
            st.markdown(f"**Via strategies:** {via}")
        for chain in rec.get("chains") or []:
            st.markdown(f"- {chain}")


# ---------------------------------------------------------------------------
# Screen 3 helpers — Graph Explorer ("wow screen"). Same reason as Screen 2:
# defs must live above the if/elif chain.
# ---------------------------------------------------------------------------

@st.cache_data(ttl=600)
def _search_candidates(term: str) -> list[dict]:
    """Search Movie.title and Actor.name (case-insensitive substring).

    Returns up to 10 movies + 10 actors. Movies sorted alphabetically; actors
    sorted by film-count descending so high-signal hits surface first.
    """
    term = term.strip()
    if len(term) < 2:
        return []
    return safe_run_query(
        """
        MATCH (m:Movie) WHERE toLower(m.title) CONTAINS toLower($q)
        RETURN 'Movie' AS kind,
               toString(m.movieId) AS id,
               m.title AS label,
               coalesce(toString(m.year), '?') AS disambiguator
        ORDER BY m.title
        LIMIT 10
        UNION ALL
        MATCH (a:Actor) WHERE toLower(a.name) CONTAINS toLower($q)
        OPTIONAL MATCH (a)<-[:FEATURES_ACTOR]-(film:Movie)
        WITH a, count(DISTINCT film) AS film_count
        RETURN 'Actor' AS kind,
               a.name AS id,
               a.name AS label,
               toString(film_count) + ' films' AS disambiguator
        ORDER BY film_count DESC
        LIMIT 10
        """,
        {"q": term},
    )


@st.cache_data(ttl=600)
def _fetch_movie_subgraph(movie_id: int) -> dict:
    """Structured local subgraph for a Movie entry point.

    Three sequential queries (clearer than one mega-Cypher; same end shape):
      1. anchor + genres + director + top-5 actors by billing_order
      2. director's other films (top-5 by year desc) — skipped if no director
      3. each top-actor's other films (top-3, billing ≤ 3) — skipped if no actors

    Caps keep node count in the ~25-40 range — readable for pyvis.
    """
    anchor_rows = safe_run_query(
        """
        MATCH (m:Movie {movieId: $movie_id})
        OPTIONAL MATCH (m)-[:IN_GENRE]->(g:Genre)
        WITH m, collect(DISTINCT g.name) AS genres
        OPTIONAL MATCH (m)-[:DIRECTED_BY]->(d:Director)
        WITH m, genres, d.name AS director
        OPTIONAL MATCH (m)-[fa:FEATURES_ACTOR]->(a:Actor)
        WITH m, genres, director, a, fa.billing_order AS billing
        ORDER BY billing ASC
        WITH m, genres, director,
             [x IN collect({name: a.name, billing: billing}) WHERE x.name IS NOT NULL][..5] AS top_actors
        RETURN m.movieId AS movieId,
               m.title   AS title,
               m.year    AS year,
               genres,
               director,
               top_actors
        """,
        {"movie_id": movie_id},
    )
    if not anchor_rows:
        return {}
    bundle = anchor_rows[0]

    if bundle.get("director"):
        bundle["director_other_films"] = safe_run_query(
            """
            MATCH (d:Director {name: $name})<-[:DIRECTED_BY]-(of:Movie)
            WHERE of.movieId <> $movie_id
            WITH of ORDER BY of.year DESC LIMIT 5
            RETURN of.movieId AS id, of.title AS title, of.year AS year
            """,
            {"name": bundle["director"], "movie_id": movie_id},
        )
    else:
        bundle["director_other_films"] = []

    if bundle["top_actors"]:
        bundle["actor_other_films"] = safe_run_query(
            """
            UNWIND $actor_names AS actor_name
            OPTIONAL MATCH (a:Actor {name: actor_name})<-[fa:FEATURES_ACTOR]-(af:Movie)
            WHERE af.movieId <> $movie_id AND fa.billing_order <= 3
            WITH actor_name, af ORDER BY af.year DESC
            WITH actor_name,
                 [x IN collect({id: af.movieId, title: af.title, year: af.year})
                  WHERE x.id IS NOT NULL][..3] AS films
            RETURN actor_name AS actor, films
            """,
            {"actor_names": [ta["name"] for ta in bundle["top_actors"]], "movie_id": movie_id},
        )
    else:
        bundle["actor_other_films"] = []

    return bundle


@st.cache_data(ttl=600)
def _fetch_actor_subgraph(actor_name: str) -> dict:
    """Structured local subgraph for an Actor entry point.

    Three sequential queries:
      1. anchor + top-5 movies they're billed in (by billing_order)
      2. per-movie director + 3 genres + top-3 co-actors (excluding entry)
      3. top-5 frequent co-stars via :COLLABORATED_WITH (movie_count >= 3,
         excluding any actor already drawn from phase 2)
    """
    anchor_rows = safe_run_query(
        """
        MATCH (a:Actor {name: $name})
        OPTIONAL MATCH (a)<-[fa:FEATURES_ACTOR]-(m:Movie)
        WITH a, m, fa.billing_order AS billing
        ORDER BY billing ASC
        WITH a,
             [x IN collect({id: m.movieId, title: m.title, year: m.year, billing: billing})
              WHERE x.id IS NOT NULL][..5] AS top_movies
        RETURN a.name AS actor_name, top_movies
        """,
        {"name": actor_name},
    )
    if not anchor_rows:
        return {}
    bundle = anchor_rows[0]

    if not bundle["top_movies"]:
        bundle["movie_details"] = []
        bundle["collaborators"] = []
        return bundle

    movie_ids = [m["id"] for m in bundle["top_movies"]]
    bundle["movie_details"] = safe_run_query(
        """
        UNWIND $movie_ids AS mid
        MATCH (m:Movie {movieId: mid})
        OPTIONAL MATCH (m)-[:DIRECTED_BY]->(d:Director)
        WITH m, d.name AS director
        OPTIONAL MATCH (m)-[:IN_GENRE]->(g:Genre)
        WITH m, director, collect(DISTINCT g.name)[..3] AS genres
        OPTIONAL MATCH (m)-[fa:FEATURES_ACTOR]->(coa:Actor)
        WHERE coa.name <> $entry_actor
        WITH m, director, genres, coa, fa.billing_order AS billing
        ORDER BY billing ASC
        WITH m, director, genres,
             [x IN collect({name: coa.name, billing: billing}) WHERE x.name IS NOT NULL][..3] AS co_actors
        RETURN m.movieId AS id, m.title AS title, director, genres, co_actors
        """,
        {"movie_ids": movie_ids, "entry_actor": actor_name},
    )

    bundle["collaborators"] = safe_run_query(
        """
        MATCH (a:Actor {name: $name})-[c:COLLABORATED_WITH]-(other:Actor)
        WHERE c.movie_count >= 3
        WITH other, c.movie_count AS movie_count
        ORDER BY movie_count DESC
        LIMIT 8
        RETURN other.name AS name, movie_count
        """,
        {"name": actor_name},
    )

    return bundle


def _render_subgraph(kind: str, bundle: dict) -> str:
    """Build a pyvis Network from a subgraph bundle, return HTML.

    Entry-point node is bigger and bordered. One color per node label
    (`_NODE_COLORS`). Edge labels show the relationship type. Hover tooltips
    surface secondary detail (billing order, collaboration count, year).
    """
    net = Network(height="650px", width="100%", bgcolor="#0e1117", font_color="white")
    net.toggle_physics(True)

    seen: set[str] = set()

    def add_node(node_id, label, color, size=16, title=None, border_width=1):
        if node_id in seen:
            return
        seen.add(node_id)
        net.add_node(
            node_id,
            label=label,
            color=color,
            size=size,
            title=title or label,
            shape="dot",
            borderWidth=border_width,
        )

    def add_edge(u, v, label, color="#888888"):
        if u in seen and v in seen:
            net.add_edge(u, v, label=label, color=color)

    if kind == "Movie":
        entry_id = f"m_{bundle['movieId']}"
        entry_label = f"{bundle['title']} ({bundle.get('year') or '?'})"
        add_node(entry_id, entry_label, _NODE_COLORS["Movie"], size=30,
                 title=f"Entry: {entry_label}", border_width=3)

        for g in bundle.get("genres") or []:
            gid = f"g_{g}"
            add_node(gid, g, _NODE_COLORS["Genre"], size=14)
            add_edge(entry_id, gid, "IN_GENRE")

        director = bundle.get("director")
        if director:
            did = f"d_{director}"
            add_node(did, director, _NODE_COLORS["Director"], size=20)
            add_edge(entry_id, did, "DIRECTED_BY")

        for ta in bundle.get("top_actors") or []:
            aid = f"a_{ta['name']}"
            add_node(aid, ta["name"], _NODE_COLORS["Actor"], size=18,
                     title=f"{ta['name']} (billing #{ta['billing']})")
            add_edge(entry_id, aid, "FEATURES_ACTOR")

        for of in bundle.get("director_other_films") or []:
            mid = f"m_{of['id']}"
            label = f"{of['title']} ({of.get('year') or '?'})"
            add_node(mid, label, _NODE_COLORS["Movie"], size=14)
            add_edge(f"d_{director}", mid, "DIRECTED_BY")

        for record in bundle.get("actor_other_films") or []:
            aid = f"a_{record['actor']}"
            for film in record.get("films") or []:
                mid = f"m_{film['id']}"
                label = f"{film['title']} ({film.get('year') or '?'})"
                add_node(mid, label, _NODE_COLORS["Movie"], size=14)
                add_edge(aid, mid, "FEATURES_ACTOR")

    elif kind == "Actor":
        entry_name = bundle["actor_name"]
        entry_id = f"a_{entry_name}"
        add_node(entry_id, entry_name, _NODE_COLORS["Actor"], size=30,
                 title=f"Entry: {entry_name}", border_width=3)

        for tm in bundle.get("top_movies") or []:
            mid = f"m_{tm['id']}"
            label = f"{tm['title']} ({tm.get('year') or '?'})"
            add_node(mid, label, _NODE_COLORS["Movie"], size=18,
                     title=f"{label} (billed #{tm['billing']})")
            add_edge(entry_id, mid, "FEATURES_ACTOR")

        for md in bundle.get("movie_details") or []:
            mid = f"m_{md['id']}"
            if md.get("director"):
                did = f"d_{md['director']}"
                add_node(did, md["director"], _NODE_COLORS["Director"], size=16)
                add_edge(mid, did, "DIRECTED_BY")
            for g in md.get("genres") or []:
                gid = f"g_{g}"
                add_node(gid, g, _NODE_COLORS["Genre"], size=12)
                add_edge(mid, gid, "IN_GENRE")
            for coa in md.get("co_actors") or []:
                aid = f"a_{coa['name']}"
                add_node(aid, coa["name"], _NODE_COLORS["Actor"], size=14,
                         title=f"{coa['name']} (billing #{coa['billing']})")
                add_edge(mid, aid, "FEATURES_ACTOR")

        for collab in bundle.get("collaborators") or []:
            aid = f"a_{collab['name']}"
            add_node(aid, collab["name"], _NODE_COLORS["Actor"], size=18,
                     title=f"{collab['name']} — collaborated {collab['movie_count']}×")
            add_edge(entry_id, aid, f"COLLAB ×{collab['movie_count']}", color="#aaccff")

    tmp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html", encoding="utf-8")
    net.write_html(tmp.name, notebook=False, open_browser=False)
    with open(tmp.name, "r", encoding="utf-8") as f:
        return f.read()


if screen == "User Profile":
    st.title("User Profile")
    user_id = st.number_input("User ID", min_value=1, max_value=943, value=196, step=1)

    with st.spinner(f"Loading user {user_id}…"):
        ratings = _fetch_ratings(int(user_id))

    if not ratings:
        st.info(
            f"User {user_id} has no ratings in the graph. "
            "Pick a user between 1 and 943, or re-run the loader notebooks (03–07)."
        )
    else:
        st.subheader(f"Rating History — {len(ratings)} ratings")
        st.dataframe(ratings, use_container_width=True, hide_index=True)

        st.subheader("Immediate KG Neighborhood")
        st.caption(
            "Depth-1 from this user: their Occupation, Gender, and top-15 rated movies. "
            "Edge labels show the relationship type."
        )
        with st.spinner("Rendering subgraph…"):
            bundle = _fetch_neighborhood(int(user_id), top_n=15)
            html = _render_neighborhood(bundle)
            components.html(html, height=520)


# ---------------------------------------------------------------------------
# Screen 2 — Recommendation Engine
# ---------------------------------------------------------------------------
elif screen == "Recommendation Engine":
    st.title("Recommendation Engine")
    st.caption(
        "Pick a user and a strategy; results come from the unified "
        "`get_recommendations()` interface in `src/recommender.py`. Each rec "
        "expands to its explainability path."
    )

    col_uid, col_strat, col_limit = st.columns([1, 2, 1])
    with col_uid:
        user_id = st.number_input("User ID", min_value=1, max_value=943, value=196, step=1)
    with col_strat:
        strategy_name = st.selectbox("Strategy", list(STRATEGIES.keys()))
    with col_limit:
        limit = st.number_input("How many?", min_value=1, max_value=50, value=10, step=1)

    if st.button("Get Recommendations", type="primary"):
        with st.spinner(f"Running {strategy_name}…"):
            recs = _fetch_recommendations(int(user_id), strategy_name, int(limit))
        st.session_state.rec_payload = (recs, strategy_name, int(user_id))

    payload = st.session_state.get("rec_payload")
    if payload is None:
        st.info(
            "Pick a user, strategy, and limit above, then click "
            "**Get Recommendations**. Results plus the per-rec explainability path "
            "will render here."
        )
    else:
        recs, strat_used, uid_used = payload

        if not recs:
            st.info(
                f"No recommendations returned for user {uid_used} via {strat_used}. "
                "Possible causes: user has no ratings (cold start), or the strategy's "
                "internal filters excluded all candidates. Try a different user or "
                "switch to Genre Affinity (most lenient cold-start behavior)."
            )
        else:
            st.subheader(f"Top {len(recs)} via {strat_used} (user {uid_used})")

            table_rows = [
                {
                    "title": r["title"],
                    "year": r.get("year"),
                    "score": round(float(r["score"]), 3),
                }
                for r in recs
            ]
            st.dataframe(table_rows, use_container_width=True, hide_index=True)

            st.subheader("Why these recommendations?")
            for i, rec in enumerate(recs, 1):
                label = f"{i}. {rec['title']} — score {round(float(rec['score']), 3)}"
                with st.expander(label):
                    _render_explanation(strat_used, rec)


# ---------------------------------------------------------------------------
# Screen 3 — Graph Explorer ("wow screen")
# ---------------------------------------------------------------------------
elif screen == "Graph Explorer":
    st.title("Graph Explorer")
    st.caption(
        "Free-form search across the knowledge graph. Pick a **movie** or **actor**, "
        "then we render their local subgraph — multi-hop neighbors that show how "
        "they connect to the rest of the catalog. Hover any node for details; "
        "drag to rearrange."
    )

    term = st.text_input("Search for a movie or actor", placeholder="e.g. Toy Story, Tom Hanks")

    if st.button("Search", type="primary") and term.strip():
        with st.spinner("Searching…"):
            st.session_state.explorer_candidates = _search_candidates(term)
        st.session_state.explorer_subgraph_html = None
        st.session_state.explorer_subgraph_label = None

    candidates = st.session_state.get("explorer_candidates")
    if candidates is None:
        st.info(
            "Type a movie or actor name (minimum 2 characters) and click **Search**. "
            "Try *Toy Story*, *Tom Hanks*, *Pulp Fiction*, *Robert De Niro*. "
            "Pick a candidate from the list, then **Show Subgraph** to render their "
            "local KG neighborhood."
        )
    else:
        if not candidates:
            st.info(
                "No matches. Try a shorter or differently-spelled term. "
                "Movies are searched on `title` (case-insensitive substring); "
                "actors on `name`. Minimum 2 characters."
            )
        else:
            options = [
                f"{c['kind']}: {c['label']} ({c['disambiguator']})"
                for c in candidates
            ]
            choice = st.selectbox(
                f"Found {len(candidates)} match{'es' if len(candidates) != 1 else ''} — pick one:",
                options,
                key="explorer_choice",
            )

            if st.button("Show Subgraph"):
                picked = candidates[options.index(choice)]
                with st.spinner(f"Building subgraph for {picked['kind']} '{picked['label']}'…"):
                    if picked["kind"] == "Movie":
                        bundle = _fetch_movie_subgraph(int(picked["id"]))
                    else:
                        bundle = _fetch_actor_subgraph(picked["id"])

                    if not bundle:
                        st.warning(
                            f"{picked['kind']} '{picked['label']}' was found but has "
                            "no neighbors in the loaded graph. Re-run the loader "
                            "notebooks (04 → 07) if this is unexpected."
                        )
                        st.session_state.explorer_subgraph_html = None
                        st.session_state.explorer_subgraph_label = None
                    else:
                        st.session_state.explorer_subgraph_html = _render_subgraph(picked["kind"], bundle)
                        st.session_state.explorer_subgraph_label = f"{picked['kind']}: {picked['label']}"

    html = st.session_state.get("explorer_subgraph_html")
    if html:
        st.subheader(st.session_state.get("explorer_subgraph_label", "Subgraph"))
        st.caption(
            "Larger node with thicker border = the entry point. "
            "Color encodes node label: "
            "**Movie** (amber), **Director** (orange), **Actor** (purple), "
            "**Genre** (teal). Light-blue edges are derived `:COLLABORATED_WITH` "
            "(weight = shared-movie count)."
        )
        components.html(html, height=680)
