import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import re
from src.database import db

class NVIDIAProduct:
    GPU = "GPU"
    TRANSCEIVER = "TRANSCEIVER" 
    CABLING = "CABLING"
    NETWORK_CARD = "NETWORK_CARD"
    SOFTWARE = "SOFTWARE"

class NVIDIAUrls:
    BASE_URLS = {
        NVIDIAProduct.GPU: "https://www.nvidia.com/en-us/data-center/gpu/",
        NVIDIAProduct.TRANSCEIVER: "https://www.nvidia.com/en-us/networking/ethernet-adapters/transceivers/",
        NVIDIAProduct.CABLING: "https://www.nvidia.com/en-us/networking/ethernet-adapters/cables/",
        NVIDIAProduct.NETWORK_CARD: "https://www.nvidia.com/en-us/networking/ethernet-adapters/",
        NVIDIAProduct.SOFTWARE: "https://developer.nvidia.com/"
    }

class DocumentScraper:
    def __init__(self):
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str) -> str:
        """Fetch HTML content from URL"""
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""

    def extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from BeautifulSoup object"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text

    def extract_headings(self, soup: BeautifulSoup) -> List[str]:
        """Extract section headings from page"""
        headings = []
        for heading_tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            headings.extend([h.get_text().strip() for h in soup.find_all(heading_tag)])
        return headings

    async def scrape_nvidia_page(self, url: str, product_type: str) -> Dict:
        """Scrape a single NVIDIA documentation page"""
        html = await self.fetch_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "NVIDIA Documentation"
        
        # Extract content
        content = self.extract_content(soup)
        headings = self.extract_headings(soup)
        
        # Combine headings with content for better search
        full_content = f"{' '.join(headings)} {content}" if headings else content
        
        return {
            "product_type": product_type,
            "title": title_text,
            "content": full_content,
            "url": url,
            "last_updated": datetime.utcnow()
        }

    async def scrape_nvidia_docs(self, product_type: str) -> List[Dict]:
        """Scrape NVIDIA documentation for a specific product type"""
        base_url = NVIDIAUrls.BASE_URLS.get(product_type)
        if not base_url:
            print(f"No base URL found for product type: {product_type}")
            return []

        print(f"Scraping {product_type} documentation from {base_url}")
        
        # For now, we'll scrape the main page. In a real implementation,
        # you would crawl through documentation links
        document = await self.scrape_nvidia_page(base_url, product_type)
        
        return [document] if document else []

async def ingest_documents():
    """Main ingestion function"""
    scraper = DocumentScraper()
    
    async with scraper:
        all_documents = []
        
        # Scrape all product types
        for product_type in [
            NVIDIAProduct.GPU,
            NVIDIAProduct.TRANSCEIVER,
            NVIDIAProduct.CABLING,
            NVIDIAProduct.NETWORK_CARD,
            NVIDIAProduct.SOFTWARE
        ]:
            try:
                documents = await scraper.scrape_nvidia_docs(product_type)
                all_documents.extend(documents)
                print(f"Scraped {len(documents)} documents for {product_type}")
            except Exception as e:
                print(f"Error scraping {product_type}: {e}")
        
        # Store documents in MongoDB
        if all_documents and db.db:
            try:
                # Upsert documents based on URL
                operations = []
                for doc in all_documents:
                    operations.append({
                        'updateOne': {
                            'filter': {'url': doc['url']},
                            'update': {'$set': doc},
                            'upsert': True
                        }
                    })
                
                if operations:
                    result = await db.db.nvidia_docs.bulk_write(operations)
                    print(f"Upserted {result.upserted_count + result.modified_count} documents")
                    
            except Exception as e:
                print(f"Error storing documents in MongoDB: {e}")
                raise
        
        return len(all_documents)

if __name__ == "__main__":
    async def main():
        from src.database import connect_to_mongo
        await connect_to_mongo()
        count = await ingest_documents()
        print(f"Ingested {count} documents total")
    
    asyncio.run(main())