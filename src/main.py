from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.routes import docs
from src.cron.schedule import start_scheduled_tasks, stop_scheduled_tasks

app = FastAPI(
    title="NVIDIA Documentation MCP Server",
    description="Multi-Process Communication Server with NVIDIA Documentation Proxy",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Start scheduled tasks and initialize database connections on application startup"""
    from src.database import connect_to_mongo, connect_to_redis
    
    # Initialize database connections
    try:
        await connect_to_mongo()
        await connect_to_redis()
        print("Database connections established successfully")
    except Exception as e:
        print(f"Error establishing database connections: {e}")
        # Continue without databases? Or should we crash?
        # For now, we'll continue but log the error
    
    # Start the scheduler for automated document ingestion
    start_scheduled_tasks()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduled tasks on application shutdown"""
    # Stop the scheduler gracefully
    stop_scheduled_tasks()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(docs.router, prefix="/api", tags=["documentation"])

@app.get("/")
async def root():
    return {"message": "NVIDIA Documentation MCP Server is running"}

@app.get("/health")
async def health_check():
    """Comprehensive health check including database connections"""
    from src.database import check_mongo_health, check_redis_health
    
    status = {"status": "healthy"}
    
    # Check MongoDB health
    mongo_healthy = await check_mongo_health()
    status["mongodb"] = "connected" if mongo_healthy else "disconnected"
    
    # Check Redis health
    redis_healthy = await check_redis_health()
    status["redis"] = "connected" if redis_healthy else "disconnected"
    
    # Overall status is unhealthy if any critical service is down
    if not mongo_healthy or not redis_healthy:
        status["status"] = "degraded"
    
    return status

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)