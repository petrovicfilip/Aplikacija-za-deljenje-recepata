from fastapi import FastAPI, HTTPException
from app.db.neo4j_driver import init_driver, close_driver, get_driver
from app.routers.recipes import router as recipes_router
from app.routers.users import router as users_router
from app.routers.likes import router as likes_router
from app.routers.recommendations import router as recommendations_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Recipe API (Neo4j)")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
app.include_router(users_router)
app.include_router(likes_router)
app.include_router(recommendations_router)