import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from app.db.neo4j_driver import get_driver
from app.schemas.recipe import RecipeCreate, RecipeUpdate, IngredientInput, RecipeIdsRequest, RecipeLikesCountOut

router = APIRouter(prefix="/recipes", tags=["recipes"])


def norm_ingredients(items: List[IngredientInput]) -> List[dict]:
    return [{"name": it.name, "unit": it.unit, "amount": it.amount} for it in items]

def norm_wanted_names(items: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for x in items:
        if not x:
            continue
        v = x.strip().lower()
        if not v or v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


# -----------------------------
# SEARCH
# -----------------------------

@router.get("/search")
def search_recipes(
    ingredients: List[str] = Query(..., description="Ponovi parametar: ?ingredients=jaja&ingredients=sir"),
    limit: int = Query(10, ge=1, le=50),
    skip: int = Query(0, ge=0),
    driver=Depends(get_driver),
):
    wanted = norm_wanted_names(ingredients)
    if not wanted:
        raise HTTPException(status_code=400, detail="ingredients must not be empty")

    cypher = """
    WITH $wanted AS wanted
    MATCH (r:Recipe)-[rel:HAS_INGREDIENT]->(i:Ingredient)
    WHERE toLower(i.name) IN wanted
    WITH r,
         collect(DISTINCT {
           name: toLower(i.name),
           amount: rel.amount,
           unit: rel.unit
         }) AS matched,
         count(DISTINCT i) AS score
    RETURN r.id AS id,
           r.title AS title,
           matched,
           score
    ORDER BY score DESC, title ASC
    SKIP $skip
    LIMIT $limit;
    """

    with driver.session() as session:
        rows = [rec.data() for rec in session.run(cypher, wanted=wanted, skip=skip, limit=limit)]

    return {"wanted": wanted, "skip": skip, "limit": limit, "results": rows}


@router.get("/search_csv")
def search_recipes_csv(
    ingredients: str = Query(..., description="Npr: ?ingredients=jaja,sir,testenina"),
    limit: int = Query(10, ge=1, le=50),
    skip: int = Query(0, ge=0),
    driver=Depends(get_driver),
):
    wanted = norm_wanted_names(ingredients.split(","))
    if not wanted:
        raise HTTPException(status_code=400, detail="ingredients must not be empty")

    cypher = """
    WITH $wanted AS wanted
    MATCH (r:Recipe)-[rel:HAS_INGREDIENT]->(i:Ingredient)
    WHERE toLower(i.name) IN wanted
    WITH r,
         collect(DISTINCT {
           name: toLower(i.name),
           amount: rel.amount,
           unit: rel.unit
         }) AS matched,
         count(DISTINCT i) AS score
    RETURN r.id AS id,
           r.title AS title,
           matched,
           score
    ORDER BY score DESC, title ASC
    SKIP $skip
    LIMIT $limit;
    """

    with driver.session() as session:
        rows = [rec.data() for rec in session.run(cypher, wanted=wanted, skip=skip, limit=limit)]

    return {"wanted": wanted, "skip": skip, "limit": limit, "results": rows}


# -----------------------------
# POPULAR
# -----------------------------

@router.get("/popular")
def popular_recipes(
    limit: int = Query(10, ge=1, le=50),
    skip: int = Query(0, ge=0),
    driver=Depends(get_driver),
):
    cypher = """
    MATCH (r:Recipe)
    OPTIONAL MATCH (u:User)-[:LIKES]->(r)
    WITH r, count(u) AS likes
    OPTIONAL MATCH (r)-[rel:HAS_INGREDIENT]->(i:Ingredient)
    WITH r, likes, collect({
      name: i.name,
      amount: rel.amount,
      unit: rel.unit
    }) AS ingredients
    RETURN r.id AS id,
           r.title AS title,
           r.description AS description,
           likes,
           ingredients
    ORDER BY likes DESC, title ASC
    SKIP $skip
    LIMIT $limit;
    """

    with driver.session() as session:
        rows = [rec.data() for rec in session.run(cypher, skip=skip, limit=limit)]

    return {"skip": skip, "limit": limit, "results": rows}

@router.post("/by_ids")
def recipes_by_ids(payload: RecipeIdsRequest, driver=Depends(get_driver)):
    ids = [x.strip() for x in payload.ids if x and x.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="ids must not be empty")

    cypher = """
    WITH $ids AS ids
    UNWIND range(0, size(ids)-1) AS idx
    WITH idx, ids[idx] AS rid
    MATCH (r:Recipe {id: rid})
    OPTIONAL MATCH (r)-[rel:HAS_INGREDIENT]->(i:Ingredient)
    WITH idx, r, collect({
      name: i.name,
      amount: rel.amount,
      unit: rel.unit
    }) AS ingredients
    RETURN r.id AS id,
           r.title AS title,
           r.description AS description,
           ingredients
    ORDER BY idx ASC;
    """

    with driver.session() as session:
        rows = [rec.data() for rec in session.run(cypher, ids=ids)]

    return {"results": rows}

@router.get("/{recipe_id}/likes_count", response_model=RecipeLikesCountOut)
def recipe_likes_count(recipe_id: str, driver=Depends(get_driver)):
    rid = recipe_id.strip()
    if not rid:
        raise HTTPException(status_code=400, detail="recipe_id is required")

    cypher = """
    MATCH (r:Recipe {id: $rid})
    OPTIONAL MATCH (:User)-[:LIKES]->(r)
    RETURN r.id AS recipe_id, count(*) AS likes;
    """

    with driver.session() as session:
        rec = session.run(cypher, rid=rid).single()

    if not rec:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return rec.data()


# -----------------------------
# CRUD
# -----------------------------

@router.post("", status_code=201)
def create_recipe(payload: RecipeCreate, driver=Depends(get_driver)):
    rid = str(uuid.uuid4())
    title = payload.title
    description = payload.description
    ings = norm_ingredients(payload.ingredients)

    cypher = """
    CREATE (r:Recipe {id: $rid, title: $title, description: $description})
    WITH r
    UNWIND $ings AS ing
    MERGE (i:Ingredient {name: ing.name})
    MERGE (r)-[rel:HAS_INGREDIENT]->(i)
    SET rel.amount = ing.amount,
        rel.unit = ing.unit
    RETURN r.id AS id,
           r.title AS title,
           r.description AS description;
    """

    with driver.session() as session:
        rec = session.run(
            cypher,
            rid=rid,
            title=title,
            description=description,
            ings=ings
        ).single()

    return {"recipe": rec.data() if rec else None}


@router.get("")
def list_recipes(
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    driver=Depends(get_driver),
):
    cypher = """
    MATCH (r:Recipe)
    OPTIONAL MATCH (r)-[rel:HAS_INGREDIENT]->(i:Ingredient)
    WITH r, collect({
      name: i.name,
      amount: rel.amount,
      unit: rel.unit
    }) AS ingredients
    RETURN r.id AS id,
           r.title AS title,
           r.description AS description,
           ingredients
    ORDER BY title ASC
    SKIP $skip
    LIMIT $limit;
    """

    with driver.session() as session:
        rows = [rec.data() for rec in session.run(cypher, skip=skip, limit=limit)]

    return {"skip": skip, "limit": limit, "results": rows}


@router.get("/{recipe_id}")
def get_recipe(recipe_id: str, driver=Depends(get_driver)):
    rid = recipe_id.strip()
    if not rid:
        raise HTTPException(status_code=400, detail="recipe_id is required")

    cypher = """
    MATCH (r:Recipe {id: $rid})
    OPTIONAL MATCH (r)-[rel:HAS_INGREDIENT]->(i:Ingredient)
    RETURN r.id AS id,
           r.title AS title,
           r.description AS description,
           collect({
             name: i.name,
             amount: rel.amount,
             unit: rel.unit
           }) AS ingredients;
    """

    with driver.session() as session:
        rec = session.run(cypher, rid=rid).single()

    if not rec:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return rec.data()


@router.patch("/{recipe_id}")
def update_recipe(recipe_id: str, payload: RecipeUpdate, driver=Depends(get_driver)):
    rid = recipe_id.strip()
    if not rid:
        raise HTTPException(status_code=400, detail="recipe_id is required")

    # title: None => nije poslato
    # description: None => nije poslato; "" => obriši; "tekst" => setuj
    title = payload.title
    description = payload.description
    ings = norm_ingredients(payload.ingredients) if payload.ingredients is not None else None

    if title is None and payload.description is None and ings is None:
        raise HTTPException(status_code=400, detail="Nothing to update")

    if title is not None:
        cypher_title = """
        MATCH (r:Recipe {id: $rid})
        SET r.title = $title
        RETURN r.id AS id;
        """
        with driver.session() as session:
            ok = session.run(cypher_title, rid=rid, title=title).single()
        if not ok:
            raise HTTPException(status_code=404, detail="Recipe not found")

    if payload.description is not None:
        cypher_desc = """
        MATCH (r:Recipe {id: $rid})
        SET r.description = $description
        RETURN r.id AS id;
        """
        with driver.session() as session:
            ok = session.run(cypher_desc, rid=rid, description=description).single()
        if not ok:
            raise HTTPException(status_code=404, detail="Recipe not found")

    if ings is not None:
        cypher_ings = """
        MATCH (r:Recipe {id: $rid})
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
            ok = session.run(cypher_ings, rid=rid, ings=ings).single()
        if not ok:
            raise HTTPException(status_code=404, detail="Recipe not found")

    return get_recipe(rid, driver)


@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: str, driver=Depends(get_driver)):
    rid = recipe_id.strip()
    if not rid:
        raise HTTPException(status_code=400, detail="recipe_id is required")

    cypher = """
    MATCH (r:Recipe {id: $rid})
    DETACH DELETE r
    RETURN count(*) AS deleted;
    """

    with driver.session() as session:
        rec = session.run(cypher, rid=rid).single()

    if not rec or rec["deleted"] == 0:
        raise HTTPException(status_code=404, detail="Recipe not found")
