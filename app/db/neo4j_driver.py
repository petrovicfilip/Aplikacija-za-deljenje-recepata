from neo4j import GraphDatabase
from app import settings

_driver = None

def init_driver() -> None:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )

def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None

def get_driver():
    if _driver is None:
        init_driver()
    return _driver
