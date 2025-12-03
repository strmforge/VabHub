"""
测试漫画路由器注册问题
"""
import sys
from fastapi import FastAPI, APIRouter

# 模拟漫画路由器（已有前缀）
manga_sync_router = APIRouter(prefix="/api/manga/local/sync", tags=["漫画同步"])

@manga_sync_router.get("/series/{series_id}")
def sync_series(series_id: int):
    return {"message": f"同步系列 {series_id}"}

@manga_sync_router.post("/favorites")
def sync_favorites():
    return {"message": "同步收藏"}

# 创建API路由器
api_router = APIRouter()

# 测试不同的注册方式
print("=== 测试1：正确注册方式（路由器已有前缀，注册时不加prefix） ===")
app1 = FastAPI()
api_router1 = APIRouter()
api_router1.include_router(manga_sync_router, tags=["漫画同步"])  # 正确方式
app1.include_router(api_router1, prefix="/api")

openapi1 = app1.openapi()
paths1 = list(openapi1["paths"].keys())
print(f"路径数量: {len(paths1)}")
for path in paths1:
    print(f"  - {path}")

print("\n=== 测试2：错误注册方式（路由器已有前缀，注册时加prefix） ===")
app2 = FastAPI()
api_router2 = APIRouter()
api_router2.include_router(manga_sync_router, prefix="/api", tags=["漫画同步"])  # 错误方式
app2.include_router(api_router2, prefix="/api")

openapi2 = app2.openapi()
paths2 = list(openapi2["paths"].keys())
print(f"路径数量: {len(paths2)}")
for path in paths2:
    print(f"  - {path}")

print("\n=== 测试3：修复注册方式（使用prefix=\"\"） ===")
app3 = FastAPI()
api_router3 = APIRouter()
api_router3.include_router(manga_sync_router, prefix="", tags=["漫画同步"])  # 修复方式
app3.include_router(api_router3, prefix="/api")

openapi3 = app3.openapi()
paths3 = list(openapi3["paths"].keys())
print(f"路径数量: {len(paths3)}")
for path in paths3:
    print(f"  - {path}")

print("\n=== 结论 ===")
print("当路由器已有前缀时，注册时应该使用 prefix=\"\" 或者不指定prefix参数")
print("当前项目中的注册方式可能是错误的，导致路径重复")