from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException
from neo4j import GraphDatabase
import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "mojaSifra123")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

app = FastAPI(title="Recipe API (Neo4j)")

@app.on_event("shutdown")
def shutdown_event():
    driver.close()

@app.get("/health")
def health():
    try:
        with driver.session() as session:
            session.run("RETURN 1 AS ok").single()
        return {"status": "ok", "neo4j": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j connection failed: {e}")

@app.get("/recipes/search")
def search_recipes(
    ingredients: List[str] = Query(..., description="Ponovi parametar više puta: ?ingredients=jaja&ingredients=sir"),
    limit: int = Query(10, ge=1, le=50),
):
    # normalizacija: trim + lower + izbaci prazne
    wanted = [x.strip().lower() for x in ingredients if x.strip()]
    if not wanted:
        raise HTTPException(status_code=400, detail="ingredients must not be empty")

    cypher = """
    WITH $wanted AS wanted
    MATCH (r:Recipe)-[:HAS_INGREDIENT]->(i:Ingredient)
    WHERE toLower(i.name) IN wanted
    WITH r,
         collect(DISTINCT toLower(i.name)) AS matched,
         size(collect(DISTINCT i)) AS score
    RETURN r.id AS id, r.title AS title, matched, score
    ORDER BY score DESC, title ASC
    LIMIT $limit
    """

    with driver.session() as session:
        result = session.run(cypher, wanted=wanted, limit=limit)
        rows = [record.data() for record in result]

    return {"wanted": wanted, "results": rows}

@app.get("/recipes/search_csv")
def search_recipes_csv(
    ingredients: str = Query(..., description="Npr: ?ingredients=jaja,sir,testenina"),
    limit: int = Query(10, ge=1, le=50),
):
    wanted = [x.strip().lower() for x in ingredients.split(",") if x.strip()]
    if not wanted:
        raise HTTPException(status_code=400, detail="ingredients must not be empty")

    cypher = """
    WITH $wanted AS wanted
    MATCH (r:Recipe)-[:HAS_INGREDIENT]->(i:Ingredient)
    WHERE toLower(i.name) IN wanted
    WITH r,
         collect(DISTINCT toLower(i.name)) AS matched,
         size(collect(DISTINCT i)) AS score
    RETURN r.id AS id, r.title AS title, matched, score
    ORDER BY score DESC, title ASC
    LIMIT $limit
    """

    with driver.session() as session:
        result = session.run(cypher, wanted=wanted, limit=limit)
        rows = [record.data() for record in result]

    return {"wanted": wanted, "results": rows}