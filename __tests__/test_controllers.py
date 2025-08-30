import pytest
from unittest.mock import AsyncMock, patch
from bson import ObjectId
from datetime import datetime
from fastapi import HTTPException

from src.controllers.docs_controller import DocsController
from src.models.document import Document

@pytest.mark.asyncio
async def test_generate_cache_key():
    """Test cache key generation."""
    key = await DocsController.generate_cache_key("GPU", "performance", 1, 10)
    assert key == "docs_search:type:GPU:search:performance:page:1:limit:10"
    
    key = await DocsController.generate_cache_key(None, None, 2, 20)
    assert key == "docs_search:page:2:limit:20"

@pytest.mark.asyncio
@patch('src.controllers.docs_controller.redis_client')
async def test_search_documents_with_cache(mock_redis):
    """Test search documents with cache hit."""
    # Mock cache hit
    mock_redis.get = AsyncMock(return_value='[{"_id": "test123", "product_type": "GPU", "title": "Test", "content": "Test content", "url": "https://test.com", "last_updated": "2023-01-01T00:00:00"}]')
    
    documents = await DocsController.search_documents("GPU", "test")
    
    assert len(documents) == 1
    assert documents[0].product_type == "GPU"
    assert mock_redis.get.called

@pytest.mark.asyncio
@patch('src.controllers.docs_controller.redis_client')
@patch('src.controllers.docs_controller.db.db')
async def test_search_documents_no_cache(mock_db, mock_redis):
    """Test search documents with cache miss."""
    # Mock cache miss
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock()
    
    # Mock MongoDB query
    mock_cursor = AsyncMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    
    mock_doc = {
        "_id": ObjectId(),
        "product_type": "GPU",
        "title": "Test Document",
        "content": "Test content",
        "url": "https://test.com",
        "last_updated": datetime.utcnow()
    }
    
    async def async_iter():
        yield mock_doc
    
    mock_cursor.__aiter__ = lambda self: async_iter()
    mock_db.nvidia_docs.find.return_value = mock_cursor
    
    documents = await DocsController.search_documents("GPU", "test")
    
    assert len(documents) == 1
    assert documents[0].product_type == "GPU"
    assert mock_redis.setex.called

@pytest.mark.asyncio
@patch('src.controllers.docs_controller.db.db')
async def test_search_documents_database_error(mock_db):
    """Test search documents with database error."""
    mock_db.nvidia_docs.find.side_effect = Exception("Database error")
    
    with pytest.raises(HTTPException) as exc_info:
        await DocsController.search_documents("GPU", "test")
    
    assert exc_info.value.status_code == 500
    assert "Database error" in str(exc_info.value.detail)

@pytest.mark.asyncio
@patch('src.controllers.docs_controller.redis_client')
async def test_get_document_by_id_with_cache(mock_redis):
    """Test get document by ID with cache hit."""
    test_id = str(ObjectId())
    
    # Mock cache hit
    mock_redis.get = AsyncMock(return_value='{"_id": "' + test_id + '", "product_type": "GPU", "title": "Test", "content": "Test content", "url": "https://test.com", "last_updated": "2023-01-01T00:00:00"}')
    
    document = await DocsController.get_document_by_id(test_id)
    
    assert document.product_type == "GPU"
    assert str(document.id) == test_id
    assert mock_redis.get.called

@pytest.mark.asyncio
@patch('src.controllers.docs_controller.redis_client')
@patch('src.controllers.docs_controller.db.db')
async def test_get_document_by_id_no_cache(mock_db, mock_redis):
    """Test get document by ID with cache miss."""
    test_id = str(ObjectId())
    
    # Mock cache miss
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock()
    
    # Mock MongoDB query
    mock_doc = {
        "_id": ObjectId(test_id),
        "product_type": "GPU",
        "title": "Test Document",
        "content": "Test content",
        "url": "https://test.com",
        "last_updated": datetime.utcnow()
    }
    mock_db.nvidia_docs.find_one = AsyncMock(return_value=mock_doc)
    
    document = await DocsController.get_document_by_id(test_id)
    
    assert document.product_type == "GPU"
    assert str(document.id) == test_id
    assert mock_redis.setex.called

@pytest.mark.asyncio
async def test_get_document_by_id_invalid_format():
    """Test get document by ID with invalid format."""
    with pytest.raises(HTTPException) as exc_info:
        await DocsController.get_document_by_id("invalid-id")
    
    assert exc_info.value.status_code == 400
    assert "Invalid document ID format" in str(exc_info.value.detail)

@pytest.mark.asyncio
@patch('src.controllers.docs_controller.db.db')
async def test_get_document_by_id_not_found(mock_db):
    """Test get document by ID when not found."""
    test_id = str(ObjectId())
    mock_db.nvidia_docs.find_one = AsyncMock(return_value=None)
    
    with pytest.raises(HTTPException) as exc_info:
        await DocsController.get_document_by_id(test_id)
    
    assert exc_info.value.status_code == 404
    assert "Document not found" in str(exc_info.value.detail)

@pytest.mark.asyncio
@patch('src.controllers.docs_controller.db.db')
async def test_get_document_stats(mock_db):
    """Test get document statistics."""
    # Mock MongoDB operations
    mock_db.nvidia_docs.count_documents = AsyncMock(return_value=100)
    
    mock_aggregate = AsyncMock()
    async def async_aggregate():
        yield {"_id": "GPU", "count": 50}
        yield {"_id": "SOFTWARE", "count": 30}
        yield {"_id": "NETWORK_CARD", "count": 20}
    
    mock_db.nvidia_docs.aggregate.return_value = async_aggregate()
    
    mock_db.nvidia_docs.find_one = AsyncMock(return_value={
        "last_updated": datetime(2023, 1, 1)
    })
    
    stats = await DocsController.get_document_stats()
    
    assert stats["total_documents"] == 100
    assert stats["documents_by_type"]["GPU"] == 50
    assert stats["documents_by_type"]["SOFTWARE"] == 30
    assert stats["last_updated"] == datetime(2023, 1, 1)

@pytest.mark.asyncio
@patch('src.controllers.docs_controller.db.db')
async def test_get_document_stats_error(mock_db):
    """Test get document statistics with error."""
    mock_db.nvidia_docs.count_documents.side_effect = Exception("Database error")
    
    with pytest.raises(HTTPException) as exc_info:
        await DocsController.get_document_stats()
    
    assert exc_info.value.status_code == 500
    assert "Database error" in str(exc_info.value.detail)