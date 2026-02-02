import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from app.db.neo4j_driver import get_driver
from app.routers.recipes import norm_ingredients
from app.schemas.recipe import RecipeCreate, RecipeUpdate
from app.schemas.user import UserCreate, UserOut, UserCreateResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", status_code=201, response_model=UserCreateResponse)
def create_user(payload: UserCreate, driver=Depends(get_driver)):
    uid = str(uuid.uuid4())
    username = payload.username

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

@router.get("/{user_id}/recipes")
def list_user_recipes(
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

    // broj recepata usera
    CALL {
      WITH u
      OPTIONAL MATCH (u)-[:CREATED]->(r:Recipe)
      RETURN count(r) AS total
    }

    // page recepti
    CALL {
      WITH u
      OPTIONAL MATCH (u)-[:CREATED]->(r:Recipe)
      OPTIONAL MATCH (r)-[:IN_CATEGORY]->(c:Category)
      OPTIONAL MATCH (r)-[rel:HAS_INGREDIENT]->(i:Ingredient)
      WITH r, c, collect({
        name: i.name,
        amount: rel.amount,
        unit: rel.unit
      }) AS ingredients
      WITH r, c, ingredients
      ORDER BY r.title ASC
      SKIP $skip
      LIMIT $limit
      RETURN collect({
        id: r.id,
        title: r.title,
        description: r.description,
        category: c.name,
        ingredients: ingredients
      }) AS results
    }

    RETURN u.id AS user_id,
           u.username AS username,
           total,
           results;
    """

    with driver.session() as session:
        rec = session.run(cypher, uid=uid, skip=skip, limit=limit).single()

    if not rec:
        raise HTTPException(status_code=404, detail="User not found")

    data = rec.data()
    return {
        "user_id": data["user_id"],
        "username": data["username"],
        "skip": skip,
        "limit": limit,
        "total": data["total"],
        "results": [x for x in (data["results"] or []) if x["id"] is not None],
    }


@router.post("/{user_id}/recipes", status_code=201)
def create_recipe_for_user(
    user_id: str,
    payload: RecipeCreate,
    driver=Depends(get_driver),
):
    uid = user_id.strip()
    if not uid:
        raise HTTPException(status_code=400, detail="user_id is required")

    rid = str(uuid.uuid4())
    title = payload.title
    description = payload.description
    category = payload.category
    ings = norm_ingredients(payload.ingredients)

    if len(ings) == 0:
        raise HTTPException(status_code=400, detail="At least 1 ingridient is required!")

    cypher = """
    MATCH (u:User {id: $uid})
    MATCH (c:Category {name: $category})
    CREATE (r:Recipe {id: $rid, title: $title, description: $description})
    MERGE (u)-[:CREATED]->(r)
    MERGE (r)-[:IN_CATEGORY]->(c)
    WITH r
    UNWIND $ings AS ing
    MERGE (i:Ingredient {name: ing.name})
    MERGE (r)-[rel:HAS_INGREDIENT]->(i)
    SET rel.amount = ing.amount,
        rel.unit = ing.unit
    RETURN r.id AS id, r.title AS title, r.description AS description;
    """

    with driver.session() as session:
        rec = session.run(
            cypher,
            uid=uid,
            category=category,
            rid=rid,
            title=title,
            description=description,
            ings=ings,
        ).single()

    if not rec:
        raise HTTPException(status_code=400, detail="User not found or invalid category")

    return {"recipe": rec.data()}

@router.patch("/{user_id}/recipes/{recipe_id}")
def update_recipe_for_user(
    user_id: str,
    recipe_id: str,
    payload: RecipeUpdate,
    driver=Depends(get_driver),
):
    uid = user_id.strip()
    rid = recipe_id.strip()
    if not uid or not rid:
        raise HTTPException(status_code=400, detail="user_id and recipe_id are required")

    title = payload.title
    description = payload.description
    category = payload.category
    ings = norm_ingredients(payload.ingredients) if payload.ingredients is not None else None

    if title is None and payload.description is None and category is None and ings is None:
        raise HTTPException(status_code=400, detail="Nothing to update")

    # update title
    if title is not None:
        cypher_title = """
        MATCH (u:User {id: $uid})-[:CREATED]->(r:Recipe {id: $rid})
        SET r.title = $title
        RETURN r.id AS id;
        """
        with driver.session() as session:
            ok = session.run(cypher_title, uid=uid, rid=rid, title=title).single()
        if not ok:
            raise HTTPException(status_code=404, detail="Recipe not found for this user")

    # update desc
    if payload.description is not None:
        cypher_desc = """
        MATCH (u:User {id: $uid})-[:CREATED]->(r:Recipe {id: $rid})
        SET r.description = $description
        RETURN r.id AS id;
        """
        with driver.session() as session:
            ok = session.run(cypher_desc, uid=uid, rid=rid, description=description).single()
        if not ok:
            raise HTTPException(status_code=404, detail="Recipe not found for this user")

    # update categ
    if category is not None:
        cypher_cat = """
        MATCH (u:User {id: $uid})-[:CREATED]->(r:Recipe {id: $rid})
        MATCH (c:Category {name: $category})
        OPTIONAL MATCH (r)-[old:IN_CATEGORY]->(:Category)
        DELETE old
        MERGE (r)-[:IN_CATEGORY]->(c)
        RETURN r.id AS id;
        """
        with driver.session() as session:
            ok = session.run(cypher_cat, uid=uid, rid=rid, category=category).single()
        if not ok:
            # moze biti: recipe nije od usera ili category ne postoji
            check = """
            MATCH (u:User {id: $uid})-[:CREATED]->(r:Recipe {id: $rid})
            RETURN r.id AS id;
            """
            with driver.session() as session:
                owned = session.run(check, uid=uid, rid=rid).single()
            if not owned:
                raise HTTPException(status_code=404, detail="Recipe not found for this user")
            raise HTTPException(status_code=400, detail="Invalid category")

    # update ingredients
    if ings is not None:
        if not ings:
            raise HTTPException(status_code=400, detail="ingredients must not be empty")

        cypher_ings = """
        MATCH (u:User {id: $uid})-[:CREATED]->(r:Recipe {id: $rid})
        OPTIONAL MATCH (r)-[old:HAS_INGREDIENT]->(:Ingredient)
        DELETE old
        WITH r
        UNWIND $ings AS ing
        MERGE (i:Ingredient {name: ing.name})
        MERGE (r)-[rel:HAS_INGREDIENT]->(i)
        SET rel.amount = ing.amount,
            rel.unit = ing.unit
        RETURN r.id AS id;
        """
        with driver.session() as session:
            ok = session.run(cypher_ings, uid=uid, rid=rid, ings=ings).single()
        if not ok:
            raise HTTPException(status_code=404, detail="Recipe not found for this user")

    # vrati novo
    cypher_out = """
    MATCH (u:User {id: $uid})-[:CREATED]->(r:Recipe {id: $rid})
    OPTIONAL MATCH (r)-[:IN_CATEGORY]->(c:Category)
    OPTIONAL MATCH (r)-[rel:HAS_INGREDIENT]->(i:Ingredient)
    RETURN r.id AS id,
           r.title AS title,
           r.description AS description,
           c.name AS category,
           collect({name:i.name, amount:rel.amount, unit:rel.unit}) AS ingredients;
    """
    with driver.session() as session:
        rec = session.run(cypher_out, uid=uid, rid=rid).single()

    if not rec:
        raise HTTPException(status_code=404, detail="Recipe not found for this user")

    return rec.data()

@router.delete("/{user_id}/recipes/{recipe_id}", status_code=204)
def delete_recipe_for_user(user_id: str, recipe_id: str, driver=Depends(get_driver)):
    uid = user_id.strip()
    rid = recipe_id.strip()
    if not uid or not rid:
        raise HTTPException(status_code=400, detail="user_id and recipe_id are required")

    cypher = """
    MATCH (u:User {id: $uid})-[:CREATED]->(r:Recipe {id: $rid})
    DETACH DELETE r
    RETURN count(*) AS deleted;
    """
    with driver.session() as session:
        rec = session.run(cypher, uid=uid, rid=rid).single()

    if not rec or rec["deleted"] == 0:
        raise HTTPException(status_code=404, detail="Recipe not found for this user")


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

@router.delete("/{user_id}")
def delete_user(user_id: str, driver=Depends(get_driver)):
    uid = user_id.strip()
    if not uid:
        raise HTTPException(status_code=400, detail="user_id is required")

    cypher = """
    MATCH (u:User {id: $uid})
    OPTIONAL MATCH (u)-[:CREATED]->(r:Recipe)
    WITH u, [x IN collect(r) WHERE x IS NOT NULL] AS rs
    FOREACH (x IN rs | DETACH DELETE x)
    DETACH DELETE u
    RETURN size(rs) AS deleted_recipes;
    """

    with driver.session() as session:
        rec = session.run(cypher, uid=uid).single()

    if not rec:
        raise HTTPException(status_code=404, detail="User not found")

    return {"user_id": uid, "deleted_recipes": rec["deleted_recipes"]}
