from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from roleready_api.core.config import settings
from roleready_api.routes.api import router as api_router
from roleready_api.routes.api_keys import router as api_keys_router
from roleready_api.routes.teams import router as teams_router
from roleready_api.routes.public_api import router as public_api_router
from roleready_api.routes.feedback import router as feedback_router

app = FastAPI(
    title="Role Ready API",
    description="Backend API for Role Ready application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Role Ready API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include API routes
app.include_router(api_router)
app.include_router(api_keys_router)
app.include_router(teams_router)
app.include_router(public_api_router)
app.include_router(feedback_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
