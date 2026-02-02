from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from app.db.neo4j_driver import get_driver
from app.schemas.rating import RatingUpsert, RatingSummary

router = APIRouter(prefix="/ratings", tags=["ratings"])

@router.put("/{recipe_id}/rating", response_model=RatingSummary)
def upsert_rating(recipe_id: str, payload: RatingUpsert, user_id: str, driver=Depends(get_driver)):
    value = payload.value

    cypher = """
    MATCH (u:User {id: $user_id})
    MATCH (r:Recipe {id: $recipe_id})
    OPTIONAL MATCH (u)-[rt:RATED]->(r)
    WITH u, r, head(collect(rt)) AS rt
    WITH u, r, rt, CASE WHEN rt IS NULL THEN null ELSE rt.value END AS prev

    // CREATE
    FOREACH (_ IN CASE WHEN rt IS NULL THEN [1] ELSE [] END |
        CREATE (u)-[:RATED {value: $value, createdAt: datetime()}]->(r)
        SET r.rating_sum = coalesce(r.rating_sum, 0) + $value,
            r.rating_count = coalesce(r.rating_count, 0) + 1
    )

    // UPDATE
    FOREACH (_ IN CASE WHEN rt IS NULL THEN [] ELSE [1] END |
        SET rt.updatedAt = datetime(),
            rt.value = $value
        SET r.rating_sum = coalesce(r.rating_sum, 0) + ($value - prev)
    )

    WITH r, u
    OPTIONAL MATCH (u)-[mine:RATED]->(r)
    RETURN
      coalesce(r.rating_sum,0) AS rating_sum,
      coalesce(r.rating_count,0) AS rating_count,
      CASE
        WHEN coalesce(r.rating_count,0) = 0 THEN 0.0
        ELSE (1.0 * coalesce(r.rating_sum,0)) / r.rating_count
      END AS rating_avg,
      mine.value AS my_rating
    """

    try:
        with driver.session() as session:
            rec = session.run(
                cypher,
                user_id=user_id,
                recipe_id=recipe_id,
                value=value
            ).single()
            if rec is None:
                raise HTTPException(status_code=404, detail="User ili recept ne postoji.")
            return {
                "rating_sum": rec["rating_sum"],
                "rating_count": rec["rating_count"],
                "rating_avg": float(rec["rating_avg"]),
                "my_rating": rec["my_rating"],
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{recipe_id}/rating", response_model=RatingSummary)
def delete_rating(recipe_id: str, user_id: str, driver=Depends(get_driver)):
    cypher = """
    MATCH (u:User {id:$user_id})
    MATCH (r:Recipe {id:$recipe_id})
    OPTIONAL MATCH (u)-[rt:RATED]->(r)
    WITH u, r, head(collect(rt)) AS rt
    WITH u, r, rt, CASE WHEN rt IS NULL THEN null ELSE rt.value END AS prev

    FOREACH (_ IN CASE WHEN rt IS NULL THEN [] ELSE [1] END |
        DELETE rt
        SET r.rating_sum = coalesce(r.rating_sum,0) - prev,
            r.rating_count = coalesce(r.rating_count,0) - 1
    )

    WITH r, u
    OPTIONAL MATCH (u)-[mine:RATED]->(r)
    RETURN
      coalesce(r.rating_sum,0) AS rating_sum,
      coalesce(r.rating_count,0) AS rating_count,
      CASE
        WHEN coalesce(r.rating_count,0) = 0 THEN 0.0
        ELSE (1.0 * coalesce(r.rating_sum,0)) / r.rating_count
      END AS rating_avg,
      mine.value AS my_rating
    """

    try:
        with driver.session() as session:
            rec = session.run(cypher, user_id=user_id, recipe_id=recipe_id).single()
            if rec is None:
                raise HTTPException(status_code=404, detail="User ili recept ne postoji.")
            return {
                "rating_sum": rec["rating_sum"],
                "rating_count": rec["rating_count"],
                "rating_avg": float(rec["rating_avg"]),
                "my_rating": rec["my_rating"],
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{recipe_id}/rating", response_model=RatingSummary)
def get_rating(recipe_id: str, user_id: Optional[str] = None, driver=Depends(get_driver)):
    cypher = """
    MATCH (r:Recipe {id:$recipe_id})
    OPTIONAL MATCH (u:User {id:$user_id})-[mine:RATED]->(r)
    RETURN
      coalesce(r.rating_sum,0) AS rating_sum,
      coalesce(r.rating_count,0) AS rating_count,
      CASE
        WHEN coalesce(r.rating_count,0) = 0 THEN 0.0
        ELSE (1.0 * coalesce(r.rating_sum,0)) / r.rating_count
      END AS rating_avg,
      mine.value AS my_rating
    """

    try:
        with driver.session() as session:
            rec = session.run(cypher, recipe_id=recipe_id, user_id=user_id).single()
            if rec is None:
                raise HTTPException(status_code=404, detail="Recept ne postoji.")
            return {
                "rating_sum": rec["rating_sum"],
                "rating_count": rec["rating_count"],
                "rating_avg": float(rec["rating_avg"]),
                "my_rating": rec["my_rating"],
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))