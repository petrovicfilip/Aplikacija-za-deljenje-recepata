import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from app.db.neo4j_driver import get_driver
from app.schemas.user import UserCreate, UserOut, UserCreateResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", status_code=201, response_model=UserCreateResponse)
def create_user(payload: UserCreate, driver=Depends(get_driver)):
    uid = str(uuid.uuid4())
    username = payload.username  # vec strip+lower iz DTO

    cypher = """
    MERGE (u:User {username: $username})
    ON CREATE SET u.id = $uid
    RETURN u.id AS id,
           u.username AS username,
           (u.id = $uid) AS created;
    """

    with driver.session() as session:
        rec = session.run(cypher, uid=uid, username=username).single()

    if not rec:
        raise HTTPException(status_code=500, detail="Failed to create user")

    data = rec.data()
    return {"user": {"id": data["id"], "username": data["username"]}, "created": data["created"]}


@router.get("/{user_id}", response_model=UserOut)
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


@router.get("", response_model=dict)
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