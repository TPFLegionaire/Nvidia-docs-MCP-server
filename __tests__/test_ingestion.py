import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.ingestion.docs_ingest import DocumentScraper, ingest_documents, NVIDIAProduct

@pytest.mark.asyncio
async def test_document_scraper_initialization():
    """Test that DocumentScraper initializes correctly."""
    async with DocumentScraper() as scraper:
        assert scraper.session is not None
        assert scraper.timeout.total == 30

@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_fetch_page_success(mock_get):
    """Test successful page fetch."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = "<html><body>Test content</body></html>"
    mock_get.return_value.__aenter__.return_value = mock_response
    
    async with DocumentScraper() as scraper:
        content = await scraper.fetch_page("https://example.com")
        assert content == "<html><body>Test content</body></html>"

@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_fetch_page_failure(mock_get):
    """Test page fetch failure."""
    mock_get.side_effect = Exception("Connection error")
    
    async with DocumentScraper() as scraper:
        content = await scraper.fetch_page("https://example.com")
        assert content == ""

@pytest.mark.asyncio
async def test_extract_content():
    """Test content extraction from HTML."""
    scraper = DocumentScraper()
    
    html = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <script>console.log('test');</script>
            <style>body { color: black; }</style>
            <h1>Main Heading</h1>
            <p>This is a paragraph with   multiple   spaces.</p>
            <div>Another section</div>
        </body>
    </html>
    """
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    content = scraper.extract_content(soup)
    
    # Should remove scripts and styles
    assert "console.log" not in content
    assert "body { color: black; }" not in content
    
    # Should clean up whitespace
    assert "multiple   spaces" not in content
    assert "multiple spaces" in content
    
    # Should include text content
    assert "Main Heading" in content
    assert "This is a paragraph" in content

@pytest.mark.asyncio
async def test_extract_headings():
    """Test heading extraction from HTML."""
    scraper = DocumentScraper()
    
    html = """
    <html>
        <h1>Heading 1</h1>
        <h2>Heading 2</h2>
        <h3>Heading 3</h3>
        <div>Not a heading</div>
    </html>
    """
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    headings = scraper.extract_headings(soup)
    
    assert len(headings) == 3
    assert "Heading 1" in headings
    assert "Heading 2" in headings
    assert "Heading 3" in headings
    assert "Not a heading" not in headings

@pytest.mark.asyncio
@patch('src.ingestion.docs_ingest.DocumentScraper.scrape_nvidia_page')
async def test_scrape_nvidia_docs(mock_scrape_page):
    """Test scraping NVIDIA docs for a product type."""
    mock_scrape_page.return_value = {
        "product_type": "GPU",
        "title": "Test GPU Documentation",
        "content": "Test content",
        "url": "https://nvidia.com/gpu",
        "last_updated": "2023-01-01T00:00:00"
    }
    
    async with DocumentScraper() as scraper:
        documents = await scraper.scrape_nvidia_docs(NVIDIAProduct.GPU)
        
        assert len(documents) == 1
        assert documents[0]["product_type"] == "GPU"
        assert documents[0]["title"] == "Test GPU Documentation"

@pytest.mark.asyncio
@patch('src.ingestion.docs_ingest.DocumentScraper.scrape_nvidia_docs')
async def test_ingest_documents(mock_scrape_docs):
    """Test main ingestion function."""
    mock_scrape_docs.return_value = [{
        "product_type": "GPU",
        "title": "Test Document",
        "content": "Test content",
        "url": "https://test.com",
        "last_updated": "2023-01-01T00:00:00"
    }]
    
    # Mock MongoDB operations
    with patch('src.ingestion.docs_ingest.db.db') as mock_db:
        mock_bulk_write = AsyncMock()
        mock_db.nvidia_docs.bulk_write.return_value = mock_bulk_write
        mock_bulk_write.upserted_count = 1
        mock_bulk_write.modified_count = 0
        
        count = await ingest_documents()
        
        assert count == 5  # 5 product types * 1 document each
        assert mock_db.nvidia_docs.bulk_write.called

@pytest.mark.asyncio
async def test_nvidia_urls():
    """Test NVIDIA URLs configuration."""
    from src.ingestion.docs_ingest import NVIDIAUrls
    
    assert NVIDIAUrls.BASE_URLS[NVIDIAProduct.GPU] == "https://www.nvidia.com/en-us/data-center/gpu/"
    assert NVIDIAUrls.BASE_URLS[NVIDIAProduct.TRANSCEIVER] == "https://www.nvidia.com/en-us/networking/ethernet-adapters/transceivers/"
    assert NVIDIAUrls.BASE_URLS[NVIDIAProduct.CABLING] == "https://www.nvidia.com/en-us/networking/ethernet-adapters/cables/"
    assert NVIDIAUrls.BASE_URLS[NVIDIAProduct.NETWORK_CARD] == "https://www.nvidia.com/en-us/networking/ethernet-adapters/"
    assert NVIDIAUrls.BASE_URLS[NVIDIAProduct.SOFTWARE] == "https://developer.nvidia.com/"