"""
测试漫画模块路由注册问题
"""
from fastapi import FastAPI, APIRouter

# 模拟漫画同步模块
manga_sync_router = APIRouter(prefix="/api/manga/local/sync", tags=["漫画同步"])

@manga_sync_router.get("/test")
def test_endpoint():
    return {"message": "测试端点"}

# 创建FastAPI应用
app = FastAPI()

# 测试不同的注册方式
print("=== 测试1：路由器已有前缀，注册时不加prefix ===")
app1 = FastAPI()
app1.include_router(manga_sync_router, tags=["漫画同步"])

# 获取OpenAPI规范
openapi1 = app1.openapi()
paths1 = list(openapi1["paths"].keys())
print(f"路径数量: {len(paths1)}")
for path in paths1:
    print(f"  - {path}")

print("\n=== 测试2：路由器已有前缀，注册时加空prefix ===")
app2 = FastAPI()
app2.include_router(manga_sync_router, prefix="", tags=["漫画同步"])

openapi2 = app2.openapi()
paths2 = list(openapi2["paths"].keys())
print(f"路径数量: {len(paths2)}")
for path in paths2:
    print(f"  - {path}")

print("\n=== 测试3：路由器已有前缀，注册时加额外prefix ===")
app3 = FastAPI()
app3.include_router(manga_sync_router, prefix="/api", tags=["漫画同步"])

openapi3 = app3.openapi()
paths3 = list(openapi3["paths"].keys())
print(f"路径数量: {len(paths3)}")
for path in paths3:
    print(f"  - {path}")

print("\n=== 结论 ===")
print("当路由器已有前缀时，注册时不应该添加prefix参数")
print("正确的注册方式应该是：api_router.include_router(manga_sync.router, tags=['漫画同步'])")