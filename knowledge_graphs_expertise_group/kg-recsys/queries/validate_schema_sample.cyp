// =============================================================================
// T-09: Schema Validation Sample Load
// =============================================================================
// Validates the schema designed in notebooks/03_graph_schema.ipynb by loading
// a small, hand-curated subset into Neo4j BEFORE committing to the full ETL
// in T-10. Catches schema/data bugs while they are still cheap to fix.
//
// HOW TO RUN
//   1. Open Neo4j Browser, connect to your AuraDB Free instance.
//   2. Run each "Section" block below as a separate cell (paste, hit Run).
//      Run them in order — sections 5-10 depend on the constraints (1) and
//      the categorical nodes (2-4) being in place first.
//   3. After all sections, run the VALIDATION QUERIES at the bottom.
//   4. Re-run sections 2-10 once more on the same database to confirm
//      idempotency (counts in V1/V2 must not change).
//
// WHAT GETS LOADED
//   Movies:   Toy Story (1), Star Wars (50), Pulp Fiction (56), Fargo (100),
//             Godfather (127)
//   Users:    94, 99, 145, 280, 286   (each rated 3+ of the 5 movies)
//   Coverage: All 7 node labels and all 6 relationship types are exercised.
//
// EXPECTED FINAL COUNTS
//   Nodes:  User=5, Movie=5, Genre=11, Director=5, Actor=50, Occupation=3,
//           Gender=2   (76 total)
//   Edges:  FEATURES_ACTOR=50, RATED=17, IN_GENRE=16, DIRECTED_BY=5,
//           HAS_OCCUPATION=5, HAS_GENDER=5   (98 total)
//
// WARNING
//   Section 0 (commented out) wipes the entire database. Only uncomment
//   on a throwaway AuraDB instance.
// =============================================================================


// === Section 0: TEARDOWN (uncomment only on a disposable instance) ==========
// MATCH (n) DETACH DELETE n;


// === Section 1: Constraints and indexes (mirrors section 6 of the notebook) =
CREATE CONSTRAINT user_id IF NOT EXISTS
  FOR (u:User) REQUIRE u.userId IS UNIQUE;
CREATE CONSTRAINT movie_id IF NOT EXISTS
  FOR (m:Movie) REQUIRE m.movieId IS UNIQUE;
CREATE CONSTRAINT genre_name IF NOT EXISTS
  FOR (g:Genre) REQUIRE g.name IS UNIQUE;
CREATE CONSTRAINT director_name IF NOT EXISTS
  FOR (d:Director) REQUIRE d.name IS UNIQUE;
CREATE CONSTRAINT actor_name IF NOT EXISTS
  FOR (a:Actor) REQUIRE a.name IS UNIQUE;
CREATE CONSTRAINT occupation_name IF NOT EXISTS
  FOR (o:Occupation) REQUIRE o.name IS UNIQUE;
CREATE CONSTRAINT gender_name IF NOT EXISTS
  FOR (g:Gender) REQUIRE g.name IS UNIQUE;
CREATE FULLTEXT INDEX movie_title_search IF NOT EXISTS
  FOR (m:Movie) ON EACH [m.title];


// === Section 2: Genre nodes (11 — only the genres our 5 movies touch) ======
UNWIND [
  "Action", "Adventure", "Animation", "Children's", "Comedy",
  "Crime", "Drama", "Romance", "Sci-Fi", "Thriller", "War"
] AS name
MERGE (:Genre {name: name});


// === Section 3: Occupation nodes (3 — only the ones our 5 users have) ======
UNWIND ["student", "librarian", "entertainment"] AS name
MERGE (:Occupation {name: name});


// === Section 4: Gender nodes (both — even if all sample users had one) =====
UNWIND ["M", "F"] AS name
MERGE (:Gender {name: name});


// === Section 5: Movie nodes ================================================
//   Title is the clean form (year stripped — see Movie.title in §4.2).
//   tmdbId comes from data/enriched/enriched_movies.csv.
UNWIND [
  {movieId: 1,   title: "Toy Story",      year: 1995, tmdbId: 862},
  {movieId: 50,  title: "Star Wars",      year: 1977, tmdbId: 11},
  {movieId: 56,  title: "Pulp Fiction",   year: 1994, tmdbId: 680},
  {movieId: 100, title: "Fargo",          year: 1996, tmdbId: 275},
  {movieId: 127, title: "Godfather, The", year: 1972, tmdbId: 238}
] AS row
MERGE (m:Movie {movieId: row.movieId})
SET m.title = row.title, m.year = row.year, m.tmdbId = row.tmdbId;


// === Section 6: User nodes + HAS_OCCUPATION + HAS_GENDER ===================
//   Demographics come from data/raw/ml-100k/u.user.
UNWIND [
  {userId: 94,  age: 26, gender: "M", occupation: "student"},
  {userId: 99,  age: 20, gender: "M", occupation: "student"},
  {userId: 145, age: 31, gender: "M", occupation: "entertainment"},
  {userId: 280, age: 30, gender: "F", occupation: "librarian"},
  {userId: 286, age: 27, gender: "M", occupation: "student"}
] AS row
MERGE (u:User {userId: row.userId})
SET u.age = row.age
WITH u, row
MATCH (g:Gender {name: row.gender})
MERGE (u)-[:HAS_GENDER]->(g)
WITH u, row
MATCH (o:Occupation {name: row.occupation})
MERGE (u)-[:HAS_OCCUPATION]->(o);


// === Section 7: IN_GENRE edges (16 — decoded from u.item genre flags) ======
UNWIND [
  {movieId: 1,   genre: "Animation"},
  {movieId: 1,   genre: "Children's"},
  {movieId: 1,   genre: "Comedy"},
  {movieId: 50,  genre: "Action"},
  {movieId: 50,  genre: "Adventure"},
  {movieId: 50,  genre: "Romance"},
  {movieId: 50,  genre: "Sci-Fi"},
  {movieId: 50,  genre: "War"},
  {movieId: 56,  genre: "Crime"},
  {movieId: 56,  genre: "Drama"},
  {movieId: 100, genre: "Crime"},
  {movieId: 100, genre: "Drama"},
  {movieId: 100, genre: "Thriller"},
  {movieId: 127, genre: "Action"},
  {movieId: 127, genre: "Crime"},
  {movieId: 127, genre: "Drama"}
] AS row
MATCH (m:Movie {movieId: row.movieId})
MATCH (g:Genre {name: row.genre})
MERGE (m)-[:IN_GENRE]->(g);


// === Section 8: Director nodes + DIRECTED_BY edges (5) =====================
//   From enriched_movies.csv 'directors' column. No co-directors in this
//   sample — the co-director edge case will be exercised by the full T-10 load.
UNWIND [
  {movieId: 1,   director: "John Lasseter"},
  {movieId: 50,  director: "George Lucas"},
  {movieId: 56,  director: "Quentin Tarantino"},
  {movieId: 100, director: "Joel Coen"},
  {movieId: 127, director: "Francis Ford Coppola"}
] AS row
MERGE (d:Director {name: row.director})
WITH row, d
MATCH (m:Movie {movieId: row.movieId})
MERGE (m)-[:DIRECTED_BY]->(d);


// === Section 9: Actor nodes + FEATURES_ACTOR edges with billing_order (50) =
//   Top 10 cast per movie from enriched_movies.csv 'cast' column.
//   billing_order is 1-indexed: 1 = lead, 10 = tenth-billed (see §5.4).
UNWIND [
  {movieId: 1,   actors: ["Tom Hanks", "Tim Allen", "Don Rickles", "Jim Varney", "Wallace Shawn", "John Ratzenberger", "Annie Potts", "John Morris", "Erik von Detten", "Laurie Metcalf"]},
  {movieId: 50,  actors: ["Mark Hamill", "Harrison Ford", "Carrie Fisher", "Peter Cushing", "Alec Guinness", "Anthony Daniels", "Kenny Baker", "Peter Mayhew", "David Prowse", "James Earl Jones"]},
  {movieId: 56,  actors: ["John Travolta", "Samuel L. Jackson", "Uma Thurman", "Bruce Willis", "Ving Rhames", "Harvey Keitel", "Eric Stoltz", "Tim Roth", "Amanda Plummer", "Maria de Medeiros"]},
  {movieId: 100, actors: ["Frances McDormand", "William H. Macy", "Steve Buscemi", "Peter Stormare", "Harve Presnell", "John Carroll Lynch", "Kristin Rudrüd", "Bruce Bohne", "Steve Reevis", "Steve Park"]},
  {movieId: 127, actors: ["Marlon Brando", "Al Pacino", "James Caan", "Robert Duvall", "Richard S. Castellano", "Diane Keaton", "Talia Shire", "Gianni Russo", "Sterling Hayden", "John Marley"]}
] AS m_cast
UNWIND range(0, size(m_cast.actors) - 1) AS idx
WITH m_cast, idx, m_cast.actors[idx] AS actor_name
MERGE (a:Actor {name: actor_name})
WITH m_cast, a, idx + 1 AS billing
MATCH (m:Movie {movieId: m_cast.movieId})
MERGE (m)-[r:FEATURES_ACTOR]->(a)
SET r.billing_order = billing;


// === Section 10: RATED edges (17 — only ratings linking our 5 users x 5 movies)
//   Source: data/raw/ml-100k/u.data. Rating cast from int to float (see §5.1).
UNWIND [
  {userId: 94,  movieId: 1,   rating: 4.0, timestamp: 885870323},
  {userId: 94,  movieId: 50,  rating: 5.0, timestamp: 891720996},
  {userId: 94,  movieId: 100, rating: 5.0, timestamp: 885872942},
  {userId: 99,  movieId: 50,  rating: 5.0, timestamp: 885679998},
  {userId: 99,  movieId: 56,  rating: 5.0, timestamp: 885679833},
  {userId: 99,  movieId: 100, rating: 5.0, timestamp: 885678813},
  {userId: 145, movieId: 1,   rating: 3.0, timestamp: 882181396},
  {userId: 145, movieId: 50,  rating: 5.0, timestamp: 885557660},
  {userId: 145, movieId: 56,  rating: 5.0, timestamp: 875271896},
  {userId: 280, movieId: 1,   rating: 4.0, timestamp: 891700426},
  {userId: 280, movieId: 50,  rating: 3.0, timestamp: 891701027},
  {userId: 280, movieId: 100, rating: 3.0, timestamp: 891700385},
  {userId: 280, movieId: 127, rating: 5.0, timestamp: 891702544},
  {userId: 286, movieId: 1,   rating: 4.0, timestamp: 876521699},
  {userId: 286, movieId: 50,  rating: 4.0, timestamp: 875806869},
  {userId: 286, movieId: 56,  rating: 2.0, timestamp: 877531469},
  {userId: 286, movieId: 100, rating: 3.0, timestamp: 876521650}
] AS row
MATCH (u:User {userId: row.userId})
MATCH (m:Movie {movieId: row.movieId})
MERGE (u)-[r:RATED]->(m)
SET r.rating = row.rating, r.timestamp = row.timestamp;


// =============================================================================
// VALIDATION QUERIES — run each one after sections 1-10 have loaded.
// Each query corresponds to either a count check or one of the competency
// questions (CQs) from notebooks/03_graph_schema.ipynb §2.
// =============================================================================


// --- V1. Node counts by label ------------------------------------------------
// Expect: Actor=50, Genre=11, Movie=5, User=5, Director=5, Occupation=3, Gender=2
MATCH (n)
RETURN labels(n)[0] AS label, count(*) AS n
ORDER BY n DESC;


// --- V2. Relationship counts by type -----------------------------------------
// Expect: FEATURES_ACTOR=50, RATED=17, IN_GENRE=16, HAS_GENDER=5,
//         HAS_OCCUPATION=5, DIRECTED_BY=5
MATCH ()-[r]->()
RETURN type(r) AS rel, count(*) AS n
ORDER BY n DESC;


// --- V3. CQ-1.1: What has user 280 rated? -----------------------------------
MATCH (u:User {userId: 280})-[r:RATED]->(m:Movie)
RETURN m.title AS title, m.year AS year, r.rating AS rating
ORDER BY rating DESC;


// --- V4. CQ-1.3: Top genres for user 280 by average rating ------------------
MATCH (u:User {userId: 280})-[r:RATED]->(:Movie)-[:IN_GENRE]->(g:Genre)
RETURN g.name AS genre, avg(r.rating) AS avg_rating, count(*) AS n_movies
ORDER BY avg_rating DESC, genre;


// --- V5. CQ-2.1: Movies in user 280's high-rated genres they have NOT seen --
//   Expect: Pulp Fiction (the only one of our 5 movies 280 hasn't rated) shows
//   up via the Crime and Drama genre paths.
MATCH (u:User {userId: 280})-[r:RATED]->(:Movie)-[:IN_GENRE]->(g:Genre)
WITH u, g, avg(r.rating) AS score
WHERE score >= 4.0
MATCH (g)<-[:IN_GENRE]-(rec:Movie)
WHERE NOT EXISTS { MATCH (u)-[:RATED]->(rec) }
RETURN g.name AS top_genre, score, rec.title AS recommendation
ORDER BY score DESC, top_genre;


// --- V6. CQ-2.2: Movies sharing a director with 280's top-rated movie -------
//   Expect: zero rows. With 5 distinct directors in the sample there is no
//   shared-director path. A zero result here is correct — it proves the
//   traversal returns nothing when the data legitimately has nothing.
MATCH (u:User {userId: 280})-[r:RATED]->(top:Movie)-[:DIRECTED_BY]->(d:Director)
                                       <-[:DIRECTED_BY]-(rec:Movie)
WHERE r.rating = 5.0 AND rec <> top
RETURN top.title AS seed, d.name AS director, rec.title AS recommendation;


// --- V7. CQ-2.3: Collaborative — users with overlapping taste with 280 ------
//   Find users who share a movie rated 4+ with user 280.
//   Expect: 94, 99, 145, 286 all show up (they all overlap on 50, 1, 100, etc).
MATCH (u:User {userId: 280})-[r1:RATED]->(m:Movie)<-[r2:RATED]-(peer:User)
WHERE r1.rating >= 4.0 AND r2.rating >= 4.0 AND peer.userId <> 280
RETURN peer.userId AS peer, count(DISTINCT m) AS shared_high_ratings
ORDER BY shared_high_ratings DESC;


// --- V8. CQ-4.5: Full-text title search --------------------------------------
//   Expect: "Godfather, The" matches a search for "godfather".
CALL db.index.fulltext.queryNodes("movie_title_search", "godfather")
YIELD node, score
RETURN node.title AS title, score
ORDER BY score DESC;


// --- V9. FEATURES_ACTOR edge property check ----------------------------------
//   Confirm billing_order ran 1..10 for one movie.
MATCH (m:Movie {movieId: 127})-[r:FEATURES_ACTOR]->(a:Actor)
RETURN a.name AS actor, r.billing_order AS billing
ORDER BY billing;


// --- V10. Explainability path (CQ-3.2 shape) ---------------------------------
//   3 distinct short paths from user 280 to Pulp Fiction (which 280 hasn't
//   rated). Gender is excluded per §7.3 of the schema notebook.
MATCH path = (u:User {userId: 280})-[*1..4]-(m:Movie {movieId: 56})
WHERE NOT ANY(n IN nodes(path) WHERE n:Gender)
RETURN [x IN nodes(path) | coalesce(x.title, x.name, toString(x.userId))] AS path_nodes,
       length(path) AS hops
LIMIT 3;
