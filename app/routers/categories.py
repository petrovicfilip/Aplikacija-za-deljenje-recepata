from fastapi import APIRouter, Depends
from app.db.neo4j_driver import get_driver

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("")
def list_categories(driver=Depends(get_driver)):
    cypher = """
    MATCH (c:Category)
    RETURN c.name AS name
    ORDER BY name ASC;
    """
    with driver.session() as session:
        names = [r["name"] for r in session.run(cypher)]
    return {"results": names}
