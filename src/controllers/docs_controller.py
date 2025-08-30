from fastapi import HTTPException, Query
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timedelta

from src.models.document import Document
from src.database import db, redis_client

class DocsController:
    @staticmethod
    async def generate_cache_key(
        product_type: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 10
    ) -> str:
        """Generate Redis cache key for search queries"""
        key_parts = ["docs_search"]
        if product_type:
            key_parts.append(f"type:{product_type}")
        if search:
            key_parts.append(f"search:{search}")
        key_parts.append(f"page:{page}")
        key_parts.append(f"limit:{limit}")
        return ":".join(key_parts)

    @staticmethod
    async def search_documents(
        product_type: Optional[str] = Query(None, description="Filter by product type"),
        search: Optional[str] = Query(None, description="Full-text search query"),
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(10, ge=1, le=100, description="Items per page")
    ) -> List[Document]:
        """Search documents with optional filtering and full-text search"""
        
        # Generate cache key
        cache_key = await DocsController.generate_cache_key(product_type, search, page, limit)
        
        # Try to get from cache first
        if redis_client:
            try:
                cached_result = await redis_client.get(cache_key)
                if cached_result:
                    # Parse cached JSON back to Document objects
                    import json
                    cached_data = json.loads(cached_result)
                    return [Document(**doc) for doc in cached_data]
            except Exception as e:
                print(f"Cache read error: {e}")
        
        # Build MongoDB query
        query = {}
        
        if product_type:
            query["product_type"] = product_type.upper()
        
        if search:
            query["$text"] = {"$search": search}
        
        # Calculate pagination
        skip = (page - 1) * limit
        
        try:
            # Execute query
            cursor = db.db.nvidia_docs.find(query)
            cursor = cursor.skip(skip).limit(limit)
            
            documents = []
            async for doc in cursor:
                documents.append(Document(**doc))
            
            # Cache the result for 10 minutes
            if redis_client and documents:
                try:
                    # Convert documents to JSON-serializable format
                    import json
                    cache_data = json.dumps([doc.model_dump(by_alias=True) for doc in documents])
                    await redis_client.setex(cache_key, timedelta(minutes=10), cache_data)
                except Exception as e:
                    print(f"Cache write error: {e}")
            
            return documents
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def get_document_by_id(document_id: str) -> Document:
        """Get a single document by ID"""
        
        # Generate cache key
        cache_key = f"doc:{document_id}"
        
        # Try to get from cache first
        if redis_client:
            try:
                cached_result = await redis_client.get(cache_key)
                if cached_result:
                    import json
                    cached_data = json.loads(cached_result)
                    return Document(**cached_data)
            except Exception as e:
                print(f"Cache read error: {e}")
        
        try:
            # Validate ObjectId format
            if not ObjectId.is_valid(document_id):
                raise HTTPException(status_code=400, detail="Invalid document ID format")
            
            # Query MongoDB
            doc = await db.db.nvidia_docs.find_one({"_id": ObjectId(document_id)})
            
            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")
            
            document = Document(**doc)
            
            # Cache the result for 10 minutes
            if redis_client:
                try:
                    import json
                    cache_data = json.dumps(document.model_dump(by_alias=True))
                    await redis_client.setex(cache_key, timedelta(minutes=10), cache_data)
                except Exception as e:
                    print(f"Cache write error: {e}")
            
            return document
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def get_document_stats() -> dict:
        """Get statistics about documents"""
        try:
            # Get total count
            total_count = await db.db.nvidia_docs.count_documents({})
            
            # Get count by product type
            pipeline = [
                {"$group": {"_id": "$product_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            type_counts = {}
            async for result in db.db.nvidia_docs.aggregate(pipeline):
                type_counts[result["_id"]] = result["count"]
            
            # Get most recent update
            most_recent = await db.db.nvidia_docs.find_one(
                {}, 
                sort=[("last_updated", -1)]
            )
            
            last_updated = most_recent["last_updated"] if most_recent else None
            
            return {
                "total_documents": total_count,
                "documents_by_type": type_counts,
                "last_updated": last_updated
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")