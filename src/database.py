import os
from motor.motor_asyncio import AsyncIOMotorClient
from redis import asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

db = MongoDB()

async def connect_to_mongo():
    """Connect to MongoDB with connection pooling and error recovery"""
    try:
        # Configure connection pooling
        db.client = AsyncIOMotorClient(
            MONGODB_URL,
            maxPoolSize=100,  # Maximum number of connections in the pool
            minPoolSize=10,   # Minimum number of connections to maintain
            retryWrites=True, # Enable retryable writes
            socketTimeoutMS=30000,  # 30 second socket timeout
            connectTimeoutMS=10000,  # 10 second connection timeout
            serverSelectionTimeoutMS=10000  # 10 second server selection timeout
        )
        
        # Test connection
        await db.client.admin.command('ping')
        
        db.db = db.client.nvidia_docs
        
        # Create indexes for optimal performance
        print("Creating MongoDB indexes...")
        
        # Compound text index for full-text search (weights: title 10, content 1)
        await db.db.nvidia_docs.create_index([
            ("title", "text"),
            ("content", "text")
        ], weights={"title": 10, "content": 1})
        
        # Single field indexes for filtering
        await db.db.nvidia_docs.create_index([("product_type", 1)])
        await db.db.nvidia_docs.create_index([("url", 1)], unique=True)  # Unique index for URL
        await db.db.nvidia_docs.create_index([("last_updated", -1)])  # Descending for recent first
        
        # Compound index for common query patterns
        await db.db.nvidia_docs.create_index([("product_type", 1), ("last_updated", -1)])
        
        print("Connected to MongoDB and created indexes successfully")
        
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        # Implement retry logic or fallback
        raise

async def close_mongo_connection():
    """Close MongoDB connection"""
    if db.client:
        db.client.close()

async def check_mongo_health():
    """Check MongoDB connection health"""
    try:
        if db.client:
            await db.client.admin.command('ping')
            return True
        return False
    except Exception:
        return False

async def reconnect_mongo():
    """Reconnect to MongoDB with retry logic"""
    import asyncio
    
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            await close_mongo_connection()
            await connect_to_mongo()
            print(f"Successfully reconnected to MongoDB on attempt {attempt + 1}")
            return True
        except Exception as e:
            print(f"Reconnection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
    
    print("All reconnection attempts failed")
    return False

# Redis connection
redis_client = None

async def connect_to_redis():
    """Connect to Redis"""
    global redis_client
    try:
        redis_client = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        print("Connected to Redis")
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        raise

async def close_redis_connection():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()

async def check_redis_health():
    """Check Redis connection health"""
    try:
        if redis_client:
            await redis_client.ping()
            return True
        return False
    except Exception:
        return False

async def reconnect_redis():
    """Reconnect to Redis with retry logic"""
    import asyncio
    global redis_client
    
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            await close_redis_connection()
            await connect_to_redis()
            print(f"Successfully reconnected to Redis on attempt {attempt + 1}")
            return True
        except Exception as e:
            print(f"Reconnection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
    
    print("All reconnection attempts failed")
    return False