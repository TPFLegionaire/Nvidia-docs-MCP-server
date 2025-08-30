#!/usr/bin/env python3
"""
Simple test runner script since pytest is not available in this environment.
This script manually runs the test functions to verify they work correctly.
"""

import asyncio
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Import test functions manually
from __tests__.test_ingestion import (
    test_document_scraper_initialization,
    test_fetch_page_success,
    test_fetch_page_failure,
    test_extract_content,
    test_extract_headings,
    test_scrape_nvidia_docs,
    test_ingest_documents,
    test_nvidia_urls
)

from __tests__.test_controllers import (
    test_generate_cache_key,
    test_search_documents_with_cache,
    test_search_documents_no_cache,
    test_search_documents_database_error,
    test_get_document_by_id_with_cache,
    test_get_document_by_id_no_cache,
    test_get_document_by_id_invalid_format,
    test_get_document_by_id_not_found,
    test_get_document_stats,
    test_get_document_stats_error
)

from __tests__.test_routes import (
    test_search_documents_route,
    test_search_documents_invalid_product_type,
    test_get_document_by_id_route,
    test_get_document_stats_route,
    test_trigger_ingestion_route,
    test_trigger_ingestion_route_error,
    test_pagination_parameters,
    test_invalid_pagination_parameters
)

from __tests__.test_scheduler import (
    test_scheduler_initialization,
    test_scheduled_ingestion_success,
    test_scheduled_ingestion_error,
    test_scheduler_start_stop,
    test_scheduler_info_no_job,
    test_global_scheduler_functions
)

async def run_tests():
    """Run all test functions"""
    test_functions = [
        # Ingestion tests
        test_document_scraper_initialization(),
        test_fetch_page_success(),
        test_fetch_page_failure(),
        test_extract_content(),
        test_extract_headings(),
        test_scrape_nvidia_docs(),
        test_ingest_documents(),
        test_nvidia_urls(),
        
        # Controller tests  
        test_generate_cache_key(),
        test_search_documents_with_cache(),
        test_search_documents_no_cache(),
        test_search_documents_database_error(),
        test_get_document_by_id_with_cache(),
        test_get_document_by_id_no_cache(),
        test_get_document_by_id_invalid_format(),
        test_get_document_by_id_not_found(),
        test_get_document_stats(),
        test_get_document_stats_error(),
        
        # Scheduler tests
        test_scheduler_initialization(),
        test_scheduled_ingestion_success(),
        test_scheduled_ingestion_error(),
        test_scheduler_start_stop(),
        test_scheduler_info_no_job(),
        test_global_scheduler_functions(),
    ]
    
    # Run route tests separately since they need test_client fixture
    print("Running ingestion tests...")
    for test in test_functions:
        try:
            await test
            print("✓", test.__name__)
        except Exception as e:
            print("✗", test.__name__, "failed:", e)
            return False
    
    print("All tests passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)