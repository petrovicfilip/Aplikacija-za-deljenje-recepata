import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from app.db.neo4j_driver import get_driver
from app.schemas.recipe import RecipeCreate, RecipeUpdate
from app.schemas.recipe import IngredientInput

router = APIRouter(prefix="/recipes", tags=["recipes"])

def norm_ingredients(items: List[IngredientInput]) -> List[dict]:
    out = []
    seen = set()
    for it in items:
        name = it.name.strip().lower()
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)

        unit = it.unit.strip().lower() if it.unit else None
        amount = float(it.amount) if it.amount is not None else None

        out.append({"name": name, "unit": unit, "amount": amount})
    return out

def norm_wanted_names(items: List[str]) -> List[str]:
    cleaned = [x.strip().lower() for x in items if x and x.strip()]
    seen = set()
    out = []
    for x in cleaned:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

@router.get("/search")
def search_recipes(
    ingredients: List[str] = Query(...),
    limit: int = Query(10, ge=1, le=50),
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
             collect(DISTINCT {name: toLower(i.name), amount: rel.amount, unit: rel.unit}) AS matched,
             count(DISTINCT i) AS score
        RETURN r.id AS id, r.title AS title, matched, score
        ORDER BY score DESC, title ASC
        LIMIT $limit
        """

    with driver.session() as session:
        rows = [rec.data() for rec in session.run(cypher, wanted=wanted, limit=limit)]

    return {"wanted": wanted, "results": rows}


@router.get("/search_csv")
def search_recipes_csv(
    ingredients: str = Query(..., description="Npr: ?ingredients=jaja,sir,testenina"),
    limit: int = Query(10, ge=1, le=50),
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
             collect(DISTINCT {name: toLower(i.name), amount: rel.amount, unit: rel.unit}) AS matched,
             count(DISTINCT i) AS score
        RETURN r.id AS id, r.title AS title, matched, score
        ORDER BY score DESC, title ASC
        LIMIT $limit
        """

    with driver.session() as session:
        rows = [rec.data() for rec in session.run(cypher, wanted=wanted, limit=limit)]

    return {"wanted": wanted, "results": rows}

# upsert, pa idem MERGE ne CREATE
@router.post("", status_code=201)
def create_recipe(payload: RecipeCreate, driver=Depends(get_driver)):
    # rid = payload.id.strip()
    rid = str(uuid.uuid4())
    title = payload.title.strip()
    ings = norm_ingredients(payload.ingredients)
    description = payload.description.strip() if payload.description else None

    if not title or not ings:
        raise HTTPException(status_code=400, detail="title and ingredients are required")

    cypher = """
        CREATE (r:Recipe {id: $rid, title: $title, description: $description})
        WITH r
        UNWIND $ings AS ing
        MERGE (i:Ingredient {name: ing.name})
        MERGE (r)-[rel:HAS_INGREDIENT]->(i)
        SET rel.amount = ing.amount,
            rel.unit = ing.unit
        RETURN r.id AS id, r.title AS title;
        """

    with driver.session() as session:
        rec = session.run(cypher, rid=rid, title=title, description=description, ings=ings).single()

    return {"recipe": rec.data() if rec else None}

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
               r.description as description, 
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
        RETURN r.id AS id, r.title AS title, ingredients, r.description as description
        ORDER BY title ASC
        SKIP $skip
        LIMIT $limit;
        """

    with driver.session() as session:
        rows = [rec.data() for rec in session.run(cypher, skip=skip, limit=limit)]

    return {"skip": skip, "limit": limit, "results": rows}

@router.patch("/{recipe_id}")
def update_recipe(recipe_id: str, payload: RecipeUpdate, driver=Depends(get_driver)):
    rid = recipe_id.strip()
    if not rid:
        raise HTTPException(status_code=400, detail="recipe_id is required")

    title = payload.title.strip() if payload.title is not None else None

    # description:
    # - None => nije poslato (ne diraj)
    # - ""  => obriši
    # - "tekst" => setuj
    description = None
    if payload.description is not None:
        description = payload.description.strip()  # može biti ""

    # ingredients:
    # - None => nije poslato (ne diraj)
    # - [] ili prazno nakon normalizacije => error
    ings = norm_ingredients(payload.ingredients) if payload.ingredients is not None else None

    # ništa nije poslato za update
    if title is None and payload.description is None and ings is None:
        raise HTTPException(status_code=400, detail="Nothing to update")

    # --- update title ---
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

    # --- update description ---
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

    # --- update ingredients (resync veze + set amount/unit) ---
    if ings is not None:
        if not ings:
            raise HTTPException(status_code=400, detail="ingredients must not be empty")

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

    # vrati sveže stanje
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