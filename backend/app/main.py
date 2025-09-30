from app.api.routes import agent, auth, destinations, knowledge, ops
from app.core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Atlas Travel Advisor - Agentic AI Travel Planning Platform",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(agent.router, prefix=f"{settings.API_V1_STR}/agent", tags=["agent"])
app.include_router(
    destinations.router,
    prefix=f"{settings.API_V1_STR}/destinations",
    tags=["destinations"],
)
app.include_router(
    knowledge.router, prefix=f"{settings.API_V1_STR}/knowledge", tags=["knowledge"]
)
app.include_router(ops.router, prefix=f"{settings.API_V1_STR}/ops", tags=["ops"])


@app.get("/")
async def root():
    return {"message": "Atlas Travel Advisor API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
