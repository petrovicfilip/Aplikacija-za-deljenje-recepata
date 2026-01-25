from fastapi import APIRouter, Depends, HTTPException
from app.db.neo4j_driver import get_driver
from app.schemas.like import LikeCreate

router = APIRouter(prefix="/likes", tags=["likes"])

@router.post("", status_code=201)
def like_recipe(payload: LikeCreate, driver=Depends(get_driver)):
    uid = payload.user_id.strip()
    rid = payload.recipe_id.strip()
    if not uid or not rid:
        raise HTTPException(status_code=400, detail="user_id and recipe_id are required")

    cypher = """
    MATCH (u:User {id: $uid})
    MATCH (r:Recipe {id: $rid})
    MERGE (u)-[:LIKES]->(r)
    RETURN u.id AS user_id, r.id AS recipe_id;
    """

    with driver.session() as session:
        rec = session.run(cypher, uid=uid, rid=rid).single()

    if not rec:
        # ako user ili recipe ne postoje, MATCH vrati 0 redova
        raise HTTPException(status_code=404, detail="User or Recipe not found")

    return rec.data()

@router.delete("", status_code=204)
def unlike_recipe(payload: LikeCreate, driver=Depends(get_driver)):
    uid = payload.user_id.strip()
    rid = payload.recipe_id.strip()
    if not uid or not rid:
        raise HTTPException(status_code=400, detail="user_id and recipe_id are required")

    cypher = """
    MATCH (u:User {id: $uid})-[rel:LIKES]->(r:Recipe {id: $rid})
    DELETE rel
    RETURN count(rel) AS deleted;
    """

    with driver.session() as session:
        rec = session.run(cypher, uid=uid, rid=rid).single()

    if not rec or rec["deleted"] == 0:
        raise HTTPException(status_code=404, detail="Like not found")

@router.get("/users/{user_id}")
def list_user_likes(user_id: str, driver=Depends(get_driver)):
    uid = user_id.strip()
    if not uid:
        raise HTTPException(status_code=400, detail="user_id is required")

    cypher = """
    MATCH (u:User {id: $uid})-[:LIKES]->(r:Recipe)
    RETURN r.id AS id, r.title AS title, r.description AS description
    ORDER BY r.title ASC;
    """

    with driver.session() as session:
        rows = [r.data() for r in session.run(cypher, uid=uid)]

    return {"user_id": uid, "results": rows}