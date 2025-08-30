import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from redis import asyncio as aioredis
from src.main import app
from src.database import db, redis_client

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_database():
    """Set up test database connection."""
    # Connect to test MongoDB
    test_mongodb_url = "mongodb://localhost:27017/test_nvidia_docs"
    db.client = AsyncIOMotorClient(test_mongodb_url)
    db.db = db.client.test_nvidia_docs
    
    # Create indexes
    await db.db.nvidia_docs.create_index([("content", "text"), ("title", "text")])
    await db.db.nvidia_docs.create_index([("product_type", 1)])
    
    yield
    
    # Clean up
    await db.client.drop_database("test_nvidia_docs")
    db.client.close()

@pytest.fixture(scope="session")
async def test_redis():
    """Set up test Redis connection."""
    global redis_client
    redis_client = aioredis.from_url("redis://localhost:6379/1", encoding="utf-8", decode_responses=True)
    
    yield
    
    # Clean up
    await redis_client.flushdb()
    await redis_client.close()

@pytest.fixture(scope="session")
async def test_client(test_database, test_redis):
    """Create a test client for the FastAPI app."""
    from httpx import AsyncClient
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client