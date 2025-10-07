import logging, time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.db.init_db import init_db
from app.routers import health, auth, procurement, commodity_groups
from app.weaviate.bootstrap import ensure_schema
from app.weaviate.client import get_client


logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(procurement.router, prefix=settings.API_PREFIX)
app.include_router(commodity_groups.router, prefix=settings.API_PREFIX)

def _wait_for_weaviate(max_tries: int = 20, delay_s: float = 0.75) -> None:
    for attempt in range(1, max_tries + 1):
        try:
            client = get_client()
            client.collections.list_all()
            logging.info("Weaviate is ready.")
            return
        except Exception as e:
            logging.warning("Weaviate not ready yet (try %s/%s): %s", attempt, max_tries, e)
            time.sleep(delay_s)
    raise RuntimeError("Weaviate did not become ready in time")

@app.on_event("startup")
def on_startup() -> None:
    # 1) Create SQL tables
    Base.metadata.create_all(bind=engine)

    # 2) Ensure Weaviate is ready and schema exists
    _wait_for_weaviate()
    ensure_schema()

    # 3) Optionally seed database (and vector index)
    if settings.should_seed:
        logging.info("Seeding enabled (ENV=%s).", settings.ENV)
        with SessionLocal() as db:
            init_db(db)
    else:
        logging.info("Seeding disabled (ENV=%s).", settings.ENV)
        
@app.on_event("shutdown")
def on_shutdown() -> None:
    try:
        get_client().close()
    except Exception:
        pass