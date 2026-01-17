from fastapi import FastAPI, HTTPException
from app.db.neo4j_driver import init_driver, close_driver, get_driver
from app.routers.recipes import router as recipes_router

app = FastAPI(title="Recipe API (Neo4j)")

@app.on_event("startup")
def on_startup():
    init_driver()

@app.on_event("shutdown")
def on_shutdown():
    close_driver()

@app.get("/health")
def health():
    try:
        driver = get_driver()
        with driver.session() as session:
            session.run("RETURN 1 AS ok").single()
        return {"status": "ok", "neo4j": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j connection failed: {e}")

app.include_router(recipes_router)