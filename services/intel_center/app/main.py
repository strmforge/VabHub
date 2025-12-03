from fastapi import FastAPI, Query

from .store import IntelDataStore

app = FastAPI(title="VabHub Intel Center")

store: IntelDataStore = IntelDataStore()


@app.get("/v1/rules/latest")
async def get_rules_latest():
    return store.get_rules_latest()


@app.get("/v1/index/{release_key}")
async def get_release_index(release_key: str):
    return store.get_release_index(release_key)


@app.get("/v1/alias/search")
async def search_alias(q: str = Query(..., description="模糊搜索别名")):
    results = store.search_alias(q)
    return {"query": q, "results": results}


@app.get("/v1/alias/resolve")
async def resolve_alias(q: str = Query(..., description="需要解析的原始标题")):
    result = store.resolve_alias(q)
    return result or {}

