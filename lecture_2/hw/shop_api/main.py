from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from lecture_2.hw.shop_api.config import API_PREFIX, PROJECT_NAME
from lecture_2.hw.shop_api.routers import carts_router, items_router
from lecture_2.hw.shop_api.storage import init_db

app = FastAPI(title=PROJECT_NAME)
app.include_router(prefix=API_PREFIX, router=items_router, tags=["Item"])
app.include_router(prefix=API_PREFIX, router=carts_router, tags=["Cart"])
Instrumentator().instrument(app).expose(app)

init_db()
