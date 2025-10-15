from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from roleready_api.core.config import settings
from roleready_api.routes.api import router as api_router

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
