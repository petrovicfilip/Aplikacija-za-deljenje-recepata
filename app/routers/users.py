import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from app.db.neo4j_driver import get_driver
from app.schemas.user import UserCreate

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", status_code=201)
def create_user(payload: UserCreate, driver=Depends(get_driver)):
    uid = str(uuid.uuid4())
    username = payload.username.strip()

    if not username:
        raise HTTPException(status_code=400, detail="username is required")

    cypher = """
    // username unique: ako postoji, ne pravimo duplikat
    MERGE (u:User {username: $username})
    ON CREATE SET u.id = $uid
    RETURN u.id AS id, u.username AS username;
    """

    with driver.session() as session:
        rec = session.run(cypher, uid=uid, username=username).single()

    # za sad vracam postojeceg usera ako ga ima taj username
    return rec.data() if rec else None

@router.get("/{user_id}")
def get_user(user_id: str, driver=Depends(get_driver)):
    uid = user_id.strip()
    if not uid:
        raise HTTPException(status_code=400, detail="user_id is required")

    cypher = """
    MATCH (u:User {id: $uid})
    RETURN u.id AS id, u.username AS username;
    """

    with driver.session() as session:
        rec = session.run(cypher, uid=uid).single()

    if not rec:
        raise HTTPException(status_code=404, detail="User not found")

    return rec.data()

@router.get("")
def list_users(
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    driver=Depends(get_driver),
):
    cypher = """
    MATCH (u:User)
    RETURN u.id AS id, u.username AS username
    ORDER BY u.username ASC
    SKIP $skip
    LIMIT $limit;
    """

    with driver.session() as session:
        rows = [r.data() for r in session.run(cypher, skip=skip, limit=limit)]

    return {"skip": skip, "limit": limit, "results": rows}