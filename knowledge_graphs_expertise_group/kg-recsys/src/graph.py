"""Neo4j connection and query helpers."""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
        )
    return _driver


def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None


def run_query(cypher: str, parameters: dict = None) -> list[dict]:
    driver = get_driver()
    with driver.session() as session:
        result = session.run(cypher, parameters or {})
        return [record.data() for record in result]


def run_write_query(cypher: str, parameters: dict = None) -> None:
    """Execute a write Cypher statement inside a managed transaction.

    Use this for MERGE, CREATE, SET, DELETE — anything that mutates the graph.
    The managed transaction handles retries on transient errors and ensures
    the write commits before the call returns.
    """
    driver = get_driver()
    with driver.session() as session:
        session.execute_write(
            lambda tx: tx.run(cypher, parameters or {}).consume()
        )


def run_write_query_chunked(
    cypher: str,
    rows: list[dict],
    chunk_size: int = 5000,
    param_name: str = "rows",
    desc: str = "loading",
) -> None:
    """Run an UNWIND-based write query in chunks, with a tqdm progress bar.

    For large edge loads (e.g. the 100K RATED edges) sending everything in one
    UNWIND can stress AuraDB Free or hit transaction time limits. This splits
    the input into chunks and sends one managed write transaction per chunk.

    The Cypher should reference the parameter as `$<param_name>` (default `$rows`).
    """
    driver = get_driver()
    total = len(rows)
    with driver.session() as session:
        for start in tqdm(range(0, total, chunk_size), desc=desc, unit="chunk"):
            chunk = rows[start : start + chunk_size]
            session.execute_write(
                lambda tx, c=chunk: tx.run(cypher, {param_name: c}).consume()
            )
