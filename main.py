from fastapi import FastAPI
from app.routers.process_router import router as process_router
from app.routers.search_router import router as search_router
from app.core.config import settings

app = FastAPI(title="股票检索系统")

# 注册路由
app.include_router(process_router)
app.include_router(search_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
