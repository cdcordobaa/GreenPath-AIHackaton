import os
from typing import Any, Dict, List, Tuple, Optional

from neo4j import GraphDatabase, basic_auth
from dotenv import load_dotenv


load_dotenv(override=True)


NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD),
    max_connection_pool_size=10,
)


def close_driver() -> None:
    driver.close()


def run_tx(query: str, params: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    def _work(tx):
        res = tx.run(query, **params)
        records = [r.data() for r in res]
        summary = res.consume()
        safe = {
            "counters": {},
            "t_first": getattr(summary, "result_available_after", None),
            "t_consumed": getattr(summary, "result_consumed_after", None),
        }
        try:
            ctr = getattr(summary, "counters", None)
            if ctr is not None:
                attrs = [
                    "nodes_created",
                    "nodes_deleted",
                    "relationships_created",
                    "relationships_deleted",
                    "properties_set",
                    "labels_added",
                    "labels_removed",
                    "indexes_added",
                    "indexes_removed",
                    "constraints_added",
                    "constraints_removed",
                    "system_updates",
                    "contains_updates",
                ]
                safe["counters"] = {
                    k: getattr(ctr, k)
                    for k in attrs
                    if getattr(ctr, k, None) not in (None, 0, False)
                }
        except Exception:
            pass
        return records, safe

    with driver.session() as session:
        return session.execute_read(_work)


TOKENS_LOOKUP_CYPHER = """
UNWIND $tokens AS t
WITH DISTINCT toLower(t) AS tok
MATCH (ent:Entity)
WHERE
  (ent.trigger IS NOT NULL AND toLower(ent.trigger) CONTAINS tok) OR
  (ent.norm_trigger IS NOT NULL AND toLower(ent.norm_trigger) CONTAINS tok) OR
  (ent.category IS NOT NULL AND toLower(ent.category) CONTAINS tok) OR
  (ent.label IS NOT NULL AND toLower(ent.label) CONTAINS tok)
OPTIONAL MATCH (ent)-[:TRIGGERS]->(p:Permit)
OPTIONAL MATCH (p)-[:GROUNDED_IN]->(l:Law)
OPTIONAL MATCH (p)-[:ISSUED_BY]->(a:Authority)
RETURN tok AS token,
       collect(DISTINCT {type: p.type, authority: p.authority}) AS permits,
       collect(DISTINCT {ref: l.ref, title: l.title, year: l.year}) AS laws,
       collect(DISTINCT {name: a.name}) AS authorities
LIMIT 200
"""


def lookup_tokens(tokens: List[str]) -> List[Dict[str, Any]]:
    tokens = [t for t in (tokens or []) if isinstance(t, str) and t.strip()]
    if not tokens:
        return []
    records, _ = run_tx(TOKENS_LOOKUP_CYPHER, {"tokens": tokens})
    return records


# ------------------------------------------------------------
# Taxonomy inspection helpers
# ------------------------------------------------------------

def _safe_run(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    try:
        records, _ = run_tx(query, params or {})
        return records
    except Exception:
        return []


def get_label_counts(limit: Optional[int] = 100) -> List[Dict[str, Any]]:
    query = (
        "MATCH (n) UNWIND labels(n) AS label "
        "RETURN label, count(*) AS count "
        "ORDER BY count DESC, label ASC "
    )
    if isinstance(limit, int) and limit > 0:
        query += "LIMIT $limit"
        return _safe_run(query, {"limit": limit})
    return _safe_run(query, {})


def get_reltype_counts(limit: Optional[int] = 100) -> List[Dict[str, Any]]:
    query = (
        "MATCH ()-[r]->() "
        "RETURN type(r) AS type, count(*) AS count "
        "ORDER BY count DESC, type ASC "
    )
    if isinstance(limit, int) and limit > 0:
        query += "LIMIT $limit"
        return _safe_run(query, {"limit": limit})
    return _safe_run(query, {})


def get_node_type_properties() -> List[Dict[str, Any]]:
    # Neo4j 5 schema procedure
    query = (
        "CALL db.schema.nodeTypeProperties() "
        "YIELD nodeType, propertyName, propertyTypes, mandatory, writable "
        "RETURN toString(nodeType) AS nodeType, propertyName AS property, propertyTypes, mandatory, writable "
        "ORDER BY nodeType, property"
    )
    return _safe_run(query)


def get_rel_type_properties() -> List[Dict[str, Any]]:
    query = (
        "CALL db.schema.relTypeProperties() "
        "YIELD relType, propertyName, propertyTypes, mandatory, writable "
        "RETURN toString(relType) AS relType, propertyName AS property, propertyTypes, mandatory, writable "
        "ORDER BY relType, property"
    )
    return _safe_run(query)


def get_constraints() -> List[Dict[str, Any]]:
    query = (
        "SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties "
        "RETURN name, type, entityType, labelsOrTypes, properties "
        "ORDER BY name"
    )
    return _safe_run(query)


def get_indexes() -> List[Dict[str, Any]]:
    query = (
        "SHOW INDEXES YIELD name, type, entityType, labelsOrTypes, properties "
        "RETURN name, type, entityType, labelsOrTypes, properties "
        "ORDER BY name"
    )
    return _safe_run(query)


def inspect_taxonomy(
    count_limit: Optional[int] = 100,
    include_properties: bool = True,
    include_indexes: bool = True,
    include_constraints: bool = True,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "labels": get_label_counts(limit=count_limit),
        "rel_types": get_reltype_counts(limit=count_limit),
    }
    if include_properties:
        result["node_properties"] = get_node_type_properties()
        result["rel_properties"] = get_rel_type_properties()
    if include_indexes:
        result["indexes"] = get_indexes()
    if include_constraints:
        result["constraints"] = get_constraints()
    return result


# ------------------------------------------------------------
# Instrumento path fetch
# ------------------------------------------------------------

INSTRUMENTO_QUERY = """
MATCH p=()-[:TIENE_INSTRUMENTO]->()
RETURN p
LIMIT $limit
"""


def _serialize_node(n: Any) -> Dict[str, Any]:
    try:
        return {
            "id": n.element_id if hasattr(n, "element_id") else n.get("id"),
            "labels": list(n.labels) if hasattr(n, "labels") else [],
            "properties": dict(n) if hasattr(n, "items") else dict(n or {}),
        }
    except Exception:
        try:
            return {"labels": list(n.labels), "properties": dict(n)}
        except Exception:
            return {}


def _serialize_rel(r: Any) -> Dict[str, Any]:
    try:
        return {
            "id": r.element_id if hasattr(r, "element_id") else None,
            "type": r.type if hasattr(r, "type") else None,
            "start": r.start_node.element_id if hasattr(r, "start_node") else None,
            "end": r.end_node.element_id if hasattr(r, "end_node") else None,
            "properties": dict(r) if hasattr(r, "items") else {},
        }
    except Exception:
        return {"type": getattr(r, "type", None)}


def fetch_instrumento_paths(limit: int = 25) -> List[Dict[str, Any]]:
    if limit <= 0:
        limit = 25

    def _work(tx):
        res = tx.run(INSTRUMENTO_QUERY, limit=limit)
        items: List[Dict[str, Any]] = []
        for rec in res:
            p = rec.get("p")
            if p is None:
                continue
            nodes = [_serialize_node(n) for n in p.nodes]
            rels = [_serialize_rel(r) for r in p.relationships]
            items.append({"nodes": nodes, "relationships": rels})
        return items

    with driver.session() as session:
        return session.execute_read(_work)


