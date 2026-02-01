import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from app.db.neo4j_driver import get_driver
from app.schemas.recipe import RecipeCreate, RecipeUpdate, IngredientInput, RecipeIdsRequest, RecipeLikesCountOut
from app.utils.text_norm import sr_norm_latin

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
    # !!! testtttttttttttttttttt
    cypher = """
    WITH $wanted AS wanted
    MATCH (r:Recipe)-[rel:HAS_INGREDIENT]->(i:Ingredient)
    OPTIONAL MATCH (r)-[:IN_CATEGORY]->(c:Category)
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
           c.name AS category,
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
    OPTIONAL MATCH (r)-[:IN_CATEGORY]->(c:Category)
    WITH r, c,
         collect(DISTINCT {
           name: toLower(i.name),
           amount: rel.amount,
           unit: rel.unit
         }) AS matched,
         count(DISTINCT i) AS score
    RETURN r.id AS id,
           r.title AS title,
           coalesce(c.name, "uncategorized") AS category,
           matched,
           score
    ORDER BY score DESC, title ASC
    SKIP $skip
    LIMIT $limit;
    """

    with driver.session() as session:
        rows = [rec.data() for rec in session.run(cypher, wanted=wanted, skip=skip, limit=limit)]

    return {"wanted": wanted, "skip": skip, "limit": limit, "results": rows}

@router.get("/search_by_category")
def search_by_category(
    category: str = Query(..., min_length=1, description=""),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    driver=Depends(get_driver),
):
    cat = category.strip().lower()
    if not cat:
        raise HTTPException(status_code=400, detail="category must not be empty")

    cypher = """
    MATCH (c:Category {name: $cat})
    
    CALL {
      WITH c
      MATCH (r:Recipe)-[:IN_CATEGORY]->(c)
      OPTIONAL MATCH (r)-[rel:HAS_INGREDIENT]->(i:Ingredient)
      WITH r, c, collect({
        name: i.name,
        amount: rel.amount,
        unit: rel.unit
      }) AS ingredients
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
    
    CALL {
      WITH c
      MATCH (r:Recipe)-[:IN_CATEGORY]->(c)
      RETURN count(r) AS total
    }
    
    RETURN total, results;
    """

    with driver.session() as session:
        rec = session.run(cypher, cat=cat, skip=skip, limit=limit).single()

    if not rec:
        raise HTTPException(status_code=400, detail="Invalid category")

    return {
        "category": cat,
        "skip": skip,
        "limit": limit,
        "total": rec["total"],
        "results": rec["results"] or [],
    }

# imam 2 polja: description i description_norm, gde je description_norm normalizovano f-jom sr_norm_latin i nad njim je kreiran index u bazi
# radi efikasnije pretrage, iako bi i bruteforce ovde dobro radio
# description se koristi da cuva originalni opis i da prikaz bude lepsi (prikazuje slova č ć đ... velika slova i slicno)
# neo4j koristi Lucene biblioteku
@router.get("/search_by_description")
def search_by_description(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    driver=Depends(get_driver),
):
    query = sr_norm_latin(q)
    if not query:
        raise HTTPException(status_code=400, detail="q must not be empty")

    cypher = """
    CALL db.index.fulltext.queryNodes("recipeDescNormIndex", $q) YIELD node, score
    WITH node AS r, score
    OPTIONAL MATCH (r)-[:IN_CATEGORY]->(c:Category)
    OPTIONAL MATCH (r)-[rel:HAS_INGREDIENT]->(i:Ingredient)
    WITH r, c, score, collect({
      name: i.name,
      amount: rel.amount,
      unit: rel.unit
    }) AS ingredients
    RETURN r.id AS id,
           r.title AS title,
           r.description AS description,
           c.name AS category,
           score,
           ingredients
    ORDER BY score DESC, title ASC
    SKIP $skip
    LIMIT $limit;
    """

    with driver.session() as session:
        rows = [rec.data() for rec in session.run(cypher, q=query, skip=skip, limit=limit)]

    # total (za UI paginaciju)
    cypher_total = """
    CALL db.index.fulltext.queryNodes("recipeDescNormIndex", $q) YIELD node
    RETURN count(node) AS total;
    """
    with driver.session() as session:
        total = session.run(cypher_total, q=query).single()["total"]

    return {"q": query, "skip": skip, "limit": limit, "total": total, "results": rows}


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
    OPTIONAL MATCH (r)-[:IN_CATEGORY]->(c:Category)
    OPTIONAL MATCH (r)-[rel:HAS_INGREDIENT]->(i:Ingredient)
    WITH r, likes, c, collect({
      name: i.name,
      amount: rel.amount,
      unit: rel.unit
    }) AS ingredients
    RETURN r.id AS id,
           r.title AS title,
           r.description AS description,
           c.name AS category,
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
    OPTIONAL MATCH (r)-[:IN_CATEGORY]->(c:Category)
    OPTIONAL MATCH (r)-[rel:HAS_INGREDIENT]->(i:Ingredient)
    WITH idx, r, c, collect({
      name: i.name,
      amount: rel.amount,
      unit: rel.unit
    }) AS ingredients
    RETURN r.id AS id,
           r.title AS title,
           r.description AS description,
           c.name AS category,
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
    OPTIONAL MATCH (:User)-[l:LIKES]->(r)
    RETURN r.id AS recipe_id, count(l) AS likes;
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
    description_norm = sr_norm_latin(description) if description else None
    ings = norm_ingredients(payload.ingredients)
    category = payload.category

    cypher = """
    MATCH (c:Category {name: $category})
    CREATE (r:Recipe {id: $rid, title: $title, description: $description, description_norm: $description_norm})
    MERGE (r)-[:IN_CATEGORY]->(c)
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
            description_norm=description_norm,
            ings=ings,
            category=category
        ).single()

    if not rec:
        raise HTTPException(status_code=400, detail="Invalid category")

    return {"recipe": rec.data() if rec else None}


@router.get("")
def list_recipes(
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    driver=Depends(get_driver),
):
    cypher = """
    MATCH (r:Recipe)
    OPTIONAL MATCH (r)-[:IN_CATEGORY]->(c:Category)
    OPTIONAL MATCH (r)-[rel:HAS_INGREDIENT]->(i:Ingredient)
    WITH r, c, collect({
      name: i.name,
      amount: rel.amount,
      unit: rel.unit
    }) AS ingredients
    RETURN r.id AS id,
           r.title AS title,
           r.description AS description,
           c.name AS category,
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
    OPTIONAL MATCH (u:User)-[:CREATED]->(r)
    OPTIONAL MATCH (r)-[:IN_CATEGORY]->(c:Category)
    OPTIONAL MATCH (r)-[rel:HAS_INGREDIENT]->(i:Ingredient)
    RETURN r.id AS id,
           r.title AS title,
           r.description AS description,
           c.name AS category,
           { id: u.id, username: u.username } AS created_by,
           collect({ name: i.name, amount: rel.amount, unit: rel.unit }) AS ingredients;
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
    description_norm = sr_norm_latin(description) if description else None
    ings = norm_ingredients(payload.ingredients) if payload.ingredients is not None else None
    category = payload.category

    if title is None and payload.description is None and ings is None and category is None:
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
        SET r.description_norm = $description_norm
        RETURN r.id AS id;
        """
        with driver.session() as session:
            ok = session.run(cypher_desc, rid=rid, description=description, description_norm=description_norm).single()
        if not ok:
            raise HTTPException(status_code=404, detail="Recipe not found")

    if category is not None:
        cypher_cat = """
        MATCH (r:Recipe {id: $rid})
        MATCH (c:Category {name: $category})
        OPTIONAL MATCH (r)-[old:IN_CATEGORY]->(:Category)
        DELETE old
        MERGE (r)-[:IN_CATEGORY]->(c)
        RETURN r.id AS id;
        """
        with driver.session() as session:
            ok = session.run(cypher_cat, rid=rid, category=category).single()
        if not ok:
            # moze biti Recipe not found ili Category ne postoji
            # prvo proverimo da li recipe postoji
            check = """
            MATCH (r:Recipe {id: $rid})
            RETURN r.id AS id;
            """
            with driver.session() as session:
                exists = session.run(check, rid=rid).single()
            if not exists:
                raise HTTPException(status_code=404, detail="Recipe not found")
            raise HTTPException(status_code=400, detail="Invalid category")

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
