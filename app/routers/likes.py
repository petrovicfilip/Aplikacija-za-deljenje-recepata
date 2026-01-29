from fastapi import APIRouter, Depends, HTTPException
from app.db.neo4j_driver import get_driver
from app.schemas.like import LikeCreate, UserLikesIdsResponse
from app.schemas.like import LikeOut
from fastapi import Query
from app.schemas.like import UserLikesCountResponse, UserLikesIdsPageResponse

router = APIRouter(prefix="/likes", tags=["likes"])

@router.post("", status_code=201, response_model=LikeOut)
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

@router.get("/users/{user_id}", response_model=UserLikesIdsResponse)
def list_user_likes(user_id: str, driver=Depends(get_driver)):
    uid = user_id.strip()
    if not uid:
        raise HTTPException(status_code=400, detail="user_id is required")

    cypher = """
    MATCH (u:User {id: $uid})-[:LIKES]->(r:Recipe)
    RETURN r.id AS id
    ORDER BY id ASC;
    """

    with driver.session() as session:
        recipe_ids = [row["id"] for row in session.run(cypher, uid=uid)]

    return {"user_id": uid, "recipe_ids": recipe_ids}

@router.get("/users/{user_id}/count", response_model=UserLikesCountResponse)
def likes_count(user_id: str, driver=Depends(get_driver)):
    uid = user_id.strip()
    if not uid:
        raise HTTPException(status_code=400, detail="user_id is required")

    cypher = """
    MATCH (u:User {id: $uid})
    OPTIONAL MATCH (u)-[:LIKES]->(r:Recipe)
    RETURN count(r) AS total;
    """

    with driver.session() as session:
        rec = session.run(cypher, uid=uid).single()

    if not rec:
        raise HTTPException(status_code=404, detail="User not found")

    return {"user_id": uid, "total": rec["total"]}

@router.get("/users/{user_id}/ids", response_model=UserLikesIdsPageResponse)
def list_user_like_ids(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    driver=Depends(get_driver),
):
    uid = user_id.strip()
    if not uid:
        raise HTTPException(status_code=400, detail="user_id is required")

    cypher = """
    MATCH (u:User {id: $uid})

    CALL {
      WITH u
      OPTIONAL MATCH (u)-[:LIKES]->(r:Recipe)
      RETURN count(r) AS total
    }

    CALL {
      WITH u
      OPTIONAL MATCH (u)-[:LIKES]->(r:Recipe)
      RETURN r.id AS id
      ORDER BY id ASC
      SKIP $skip
      LIMIT $limit
    }

    RETURN total, [x IN collect(id) WHERE x IS NOT NULL] AS recipe_ids;
    """

    with driver.session() as session:
        rec = session.run(cypher, uid=uid, skip=skip, limit=limit).single()

    if not rec:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": uid,
        "skip": skip,
        "limit": limit,
        "total": rec["total"],
        "recipe_ids": rec["recipe_ids"] or [],
    }
