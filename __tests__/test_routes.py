import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from bson import ObjectId

@pytest.mark.asyncio
async def test_search_documents_route(test_client):
    """Test search documents route."""
    with patch('src.routes.docs.DocsController.search_documents') as mock_search:
        mock_search.return_value = []
        
        response = await test_client.get("/api/docs?product_type=GPU&search=test")
        
        assert response.status_code == 200
        mock_search.assert_called_with("GPU", "test", 1, 10)

@pytest.mark.asyncio
async def test_search_documents_invalid_product_type(test_client):
    """Test search documents with invalid product type."""
    response = await test_client.get("/api/docs?product_type=INVALID")
    
    assert response.status_code == 400
    assert "Invalid product_type" in response.text

@pytest.mark.asyncio
async def test_get_document_by_id_route(test_client):
    """Test get document by ID route."""
    test_id = str(ObjectId())
    
    with patch('src.routes.docs.DocsController.get_document_by_id') as mock_get:
        mock_doc = {
            "_id": test_id,
            "product_type": "GPU",
            "title": "Test",
            "content": "Test content",
            "url": "https://test.com",
            "last_updated": "2023-01-01T00:00:00"
        }
        mock_get.return_value = mock_doc
        
        response = await test_client.get(f"/api/docs/{test_id}")
        
        assert response.status_code == 200
        mock_get.assert_called_with(test_id)

@pytest.mark.asyncio
async def test_get_document_stats_route(test_client):
    """Test get document stats route."""
    with patch('src.routes.docs.DocsController.get_document_stats') as mock_stats:
        mock_stats.return_value = {
            "total_documents": 100,
            "documents_by_type": {"GPU": 50},
            "last_updated": "2023-01-01T00:00:00"
        }
        
        response = await test_client.get("/api/docs/stats")
        
        assert response.status_code == 200
        assert response.json()["total_documents"] == 100

@pytest.mark.asyncio
async def test_trigger_ingestion_route(test_client):
    """Test trigger ingestion route."""
    with patch('src.routes.docs.ingest_documents') as mock_ingest:
        mock_ingest.return_value = 5
        
        response = await test_client.post("/api/docs/ingest")
        
        assert response.status_code == 200
        assert response.json()["documents_processed"] == 5
        assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_trigger_ingestion_route_error(test_client):
    """Test trigger ingestion route with error."""
    with patch('src.routes.docs.ingest_documents') as mock_ingest:
        mock_ingest.side_effect = Exception("Ingestion failed")
        
        response = await test_client.post("/api/docs/ingest")
        
        assert response.status_code == 500
        assert "Ingestion failed" in response.text

@pytest.mark.asyncio
async def test_pagination_parameters(test_client):
    """Test pagination parameters in search."""
    with patch('src.routes.docs.DocsController.search_documents') as mock_search:
        mock_search.return_value = []
        
        response = await test_client.get("/api/docs?page=2&limit=20")
        
        assert response.status_code == 200
        mock_search.assert_called_with(None, None, 2, 20)

@pytest.mark.asyncio
async def test_invalid_pagination_parameters(test_client):
    """Test invalid pagination parameters."""
    response = await test_client.get("/api/docs?page=0&limit=5")
    assert response.status_code == 422  # Validation error
    
    response = await test_client.get("/api/docs?page=1&limit=200")
    assert response.status_code == 422  # Validation error