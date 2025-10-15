from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from roleready_api.core.config import settings
from roleready_api.routes import health, parse, align, rewrite


app = FastAPI(title="RoleReady API")
app.add_middleware(
CORSMiddleware,
allow_origins=settings.ALLOW_ORIGINS,
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)


app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(parse.router, prefix=settings.API_PREFIX)
app.include_router(align.router, prefix=settings.API_PREFIX)
app.include_router(rewrite.router, prefix=settings.API_PREFIX)