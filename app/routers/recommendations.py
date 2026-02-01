from fastapi import APIRouter, Depends, HTTPException, Query
from app.db.neo4j_driver import get_driver

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/{user_id}")
def recommend_for_user(
    user_id: str,
    limit: int = Query(10, ge=1, le=50),
    skip: int = Query(0, ge=0),
    driver=Depends(get_driver),
):

    uid = user_id.strip()
    if not uid:
        raise HTTPException(status_code=400, detail="user_id is required")

    cypher = """
    // Proveri da user postoji + ucitaj lajkovane
    MATCH (u:User {id: $uid})
    OPTIONAL MATCH (u)-[:LIKES]->(liked:Recipe)
    WITH collect(DISTINCT liked) AS likedRecipes

    CALL {
      // ---------- POPULAR fallback ----------
      WITH likedRecipes
      WITH likedRecipes WHERE size(likedRecipes) = 0

      MATCH (r:Recipe)
      OPTIONAL MATCH (x:User)-[:LIKES]->(r)
      WITH r, count(x) AS score

      OPTIONAL MATCH (r)-[:IN_CATEGORY]->(c:Category)
      OPTIONAL MATCH (r)-[rel:HAS_INGREDIENT]->(i:Ingredient)

      RETURN
        r.id AS id,
        r.title AS title,
        r.description AS description,
        c.name AS category,
        score AS score,
        collect(DISTINCT {
          name: i.name,
          amount: rel.amount,
          unit: rel.unit
        }) AS ingredients,
        "popular" AS mode

      UNION

      // ---------- CONTENT-based ----------
      WITH likedRecipes
      WITH likedRecipes WHERE size(likedRecipes) > 0

      UNWIND likedRecipes AS lr
      MATCH (lr)-[:HAS_INGREDIENT]->(pi:Ingredient)
      WITH likedRecipes, collect(DISTINCT toLower(pi.name)) AS profile

      MATCH (cand:Recipe)
      WHERE NOT cand IN likedRecipes

      OPTIONAL MATCH (cand)-[:IN_CATEGORY]->(c:Category)
      MATCH (cand)-[rel:HAS_INGREDIENT]->(ci:Ingredient)

      WITH cand, c, profile,
           count(DISTINCT CASE WHEN toLower(ci.name) IN profile THEN ci END) AS score,
           collect(DISTINCT {
             name: ci.name,
             amount: rel.amount,
             unit: rel.unit
           }) AS ingredients
      WHERE score > 0

      RETURN
        cand.id AS id,
        cand.title AS title,
        cand.description AS description,
        c.name AS category,
        score AS score,
        ingredients,
        "content" AS mode
    }

    RETURN id, title, description, category, score, ingredients, mode
    ORDER BY score DESC, title ASC
    SKIP $skip
    LIMIT $limit
    """

    with driver.session() as session:
        rows = [
            r.data()
            for r in session.run(
                cypher,
                uid=uid,
                limit=limit,
                skip=skip
            )
        ]

    return {"user_id": uid, "skip": skip, "limit": limit, "results": rows}