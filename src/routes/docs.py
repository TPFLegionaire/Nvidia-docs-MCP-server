from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional

from src.controllers.docs_controller import DocsController
from src.models.document import Document

router = APIRouter()

@router.get("/docs", response_model=List[Document])
async def search_documents(
    product_type: Optional[str] = Query(None, description="Filter by product type (GPU, TRANSCEIVER, CABLING, NETWORK_CARD, SOFTWARE)"),
    search: Optional[str] = Query(None, description="Full-text search query"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    Search NVIDIA documentation with optional filtering and full-text search.
    
    - **product_type**: Filter by specific NVIDIA product type
    - **search**: Full-text search across document content and titles
    - **page**: Pagination page number
    - **limit**: Number of results per page
    """
    
    # Validate product_type if provided
    if product_type:
        valid_types = ["GPU", "TRANSCEIVER", "CABLING", "NETWORK_CARD", "SOFTWARE"]
        if product_type.upper() not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid product_type. Must be one of: {', '.join(valid_types)}"
            )
    
    return await DocsController.search_documents(product_type, search, page, limit)

@router.get("/docs/{document_id}", response_model=Document)
async def get_document_by_id(document_id: str):
    """
    Get a specific NVIDIA documentation by its ID.
    
    - **document_id**: MongoDB ObjectId of the document
    """
    return await DocsController.get_document_by_id(document_id)

@router.get("/docs/stats")
async def get_document_stats():
    """
    Get statistics about the NVIDIA documentation collection.
    
    Returns total document count, count by product type, and last update timestamp.
    """
    return await DocsController.get_document_stats()

@router.post("/docs/ingest")
async def trigger_ingestion():
    """
    Manually trigger document ingestion process.
    
    This endpoint initiates the scraping and ingestion of NVIDIA documentation.
    Returns the number of documents processed.
    """
    from src.ingestion.docs_ingest import ingest_documents
    
    try:
        count = await ingest_documents()
        return {
            "message": "Ingestion completed successfully",
            "documents_processed": count,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")