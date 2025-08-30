#!/usr/bin/env python3
"""
Comprehensive API test suite for NVIDIA Documentation MCP Server
Tests Pydantic v2 compatibility, API endpoints, and database integration
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class NVIDIADocsMCPTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED {details}")
        else:
            self.failed_tests.append(f"{test_name}: {details}")
            print(f"❌ {test_name}: FAILED {details}")

    def test_basic_connectivity(self) -> bool:
        """Test basic server connectivity"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            expected_message = "NVIDIA Documentation MCP Server is running"
            
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == expected_message:
                    self.log_result("Basic Connectivity", True, f"Status: {response.status_code}")
                    return True
                else:
                    self.log_result("Basic Connectivity", False, f"Unexpected message: {data}")
                    return False
            else:
                self.log_result("Basic Connectivity", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Basic Connectivity", False, f"Connection error: {str(e)}")
            return False

    def test_health_endpoint(self) -> Dict[str, Any]:
        """Test health check endpoint and return status"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Check required fields
                required_fields = ["status", "mongodb", "redis"]
                missing_fields = [field for field in required_fields if field not in health_data]
                
                if missing_fields:
                    self.log_result("Health Check", False, f"Missing fields: {missing_fields}")
                    return {}
                
                # Log individual service status
                mongo_status = health_data.get("mongodb", "unknown")
                redis_status = health_data.get("redis", "unknown")
                overall_status = health_data.get("status", "unknown")
                
                details = f"Overall: {overall_status}, MongoDB: {mongo_status}, Redis: {redis_status}"
                self.log_result("Health Check", True, details)
                
                return health_data
            else:
                self.log_result("Health Check", False, f"Status: {response.status_code}")
                return {}
                
        except Exception as e:
            self.log_result("Health Check", False, f"Error: {str(e)}")
            return {}

    def test_docs_list_endpoint(self) -> bool:
        """Test GET /api/docs endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/docs", timeout=10)
            
            if response.status_code == 200:
                docs = response.json()
                
                # Should return a list (may be empty initially)
                if isinstance(docs, list):
                    self.log_result("Docs List", True, f"Returned {len(docs)} documents")
                    return True
                else:
                    self.log_result("Docs List", False, f"Expected list, got {type(docs)}")
                    return False
            else:
                self.log_result("Docs List", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Docs List", False, f"Error: {str(e)}")
            return False

    def test_docs_stats_endpoint(self) -> bool:
        """Test GET /api/docs/stats endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/docs/stats", timeout=10)
            
            if response.status_code == 200:
                stats = response.json()
                
                # Should return statistics object
                if isinstance(stats, dict):
                    self.log_result("Docs Stats", True, f"Stats: {json.dumps(stats, indent=2)}")
                    return True
                else:
                    self.log_result("Docs Stats", False, f"Expected dict, got {type(stats)}")
                    return False
            else:
                self.log_result("Docs Stats", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Docs Stats", False, f"Error: {str(e)}")
            return False

    def test_docs_search_with_params(self) -> bool:
        """Test GET /api/docs with query parameters"""
        test_params = [
            {"product_type": "GPU"},
            {"product_type": "SOFTWARE"},
            {"search": "nvidia"},
            {"page": 1, "limit": 5},
            {"product_type": "GPU", "search": "driver", "page": 1, "limit": 10}
        ]
        
        all_passed = True
        
        for params in test_params:
            try:
                response = requests.get(f"{self.base_url}/api/docs", params=params, timeout=10)
                
                if response.status_code == 200:
                    docs = response.json()
                    if isinstance(docs, list):
                        param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
                        self.log_result(f"Docs Search ({param_str})", True, f"Returned {len(docs)} documents")
                    else:
                        self.log_result(f"Docs Search ({param_str})", False, f"Expected list, got {type(docs)}")
                        all_passed = False
                else:
                    param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
                    self.log_result(f"Docs Search ({param_str})", False, f"Status: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
                self.log_result(f"Docs Search ({param_str})", False, f"Error: {str(e)}")
                all_passed = False
        
        return all_passed

    def test_invalid_product_type(self) -> bool:
        """Test invalid product_type parameter handling"""
        try:
            response = requests.get(f"{self.base_url}/api/docs", params={"product_type": "INVALID_TYPE"}, timeout=10)
            
            if response.status_code == 400:
                error_data = response.json()
                if "detail" in error_data and "Invalid product_type" in error_data["detail"]:
                    self.log_result("Invalid Product Type Validation", True, "Correctly rejected invalid product type")
                    return True
                else:
                    self.log_result("Invalid Product Type Validation", False, f"Unexpected error format: {error_data}")
                    return False
            else:
                self.log_result("Invalid Product Type Validation", False, f"Expected 400, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Invalid Product Type Validation", False, f"Error: {str(e)}")
            return False

    def test_docs_ingestion_endpoint(self) -> bool:
        """Test POST /api/docs/ingest endpoint (may take time)"""
        try:
            print("🔄 Testing document ingestion (this may take a while)...")
            response = requests.post(f"{self.base_url}/api/docs/ingest", timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check expected response structure
                expected_fields = ["message", "documents_processed", "status"]
                missing_fields = [field for field in expected_fields if field not in result]
                
                if missing_fields:
                    self.log_result("Docs Ingestion", False, f"Missing fields: {missing_fields}")
                    return False
                
                if result.get("status") == "success":
                    processed = result.get("documents_processed", 0)
                    self.log_result("Docs Ingestion", True, f"Processed {processed} documents")
                    return True
                else:
                    self.log_result("Docs Ingestion", False, f"Status not success: {result}")
                    return False
            else:
                self.log_result("Docs Ingestion", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            self.log_result("Docs Ingestion", False, "Request timed out (>60s)")
            return False
        except Exception as e:
            self.log_result("Docs Ingestion", False, f"Error: {str(e)}")
            return False

    def test_pydantic_model_validation(self) -> bool:
        """Test Pydantic v2 model validation by checking response structure"""
        try:
            # Get documents to test model serialization
            response = requests.get(f"{self.base_url}/api/docs?limit=1", timeout=10)
            
            if response.status_code == 200:
                docs = response.json()
                
                if len(docs) > 0:
                    doc = docs[0]
                    
                    # Check if document has expected Pydantic model fields
                    expected_fields = ["id", "product_type", "title", "content", "url", "last_updated"]
                    missing_fields = [field for field in expected_fields if field not in doc]
                    
                    if missing_fields:
                        self.log_result("Pydantic Model Validation", False, f"Missing fields: {missing_fields}")
                        return False
                    
                    # Check if ObjectId is properly serialized as string
                    doc_id = doc.get("id")
                    if isinstance(doc_id, str) and len(doc_id) == 24:
                        self.log_result("Pydantic Model Validation", True, "Document model properly serialized")
                        return True
                    else:
                        self.log_result("Pydantic Model Validation", False, f"Invalid ObjectId format: {doc_id}")
                        return False
                else:
                    self.log_result("Pydantic Model Validation", True, "No documents to validate (empty collection)")
                    return True
            else:
                self.log_result("Pydantic Model Validation", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Pydantic Model Validation", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self) -> int:
        """Run all tests and return exit code"""
        print("🚀 Starting NVIDIA Documentation MCP Server API Tests")
        print(f"📍 Testing server at: {self.base_url}")
        print("=" * 60)
        
        # Test basic connectivity first
        if not self.test_basic_connectivity():
            print("\n❌ Server not accessible. Stopping tests.")
            return 1
        
        # Test health endpoint and get database status
        health_status = self.test_health_endpoint()
        
        # Test API endpoints
        self.test_docs_list_endpoint()
        self.test_docs_stats_endpoint()
        self.test_docs_search_with_params()
        self.test_invalid_product_type()
        
        # Test Pydantic model validation
        self.test_pydantic_model_validation()
        
        # Test ingestion (may be slow)
        print("\n⚠️  Note: Ingestion test may be slow or fail if external services are unavailable")
        self.test_docs_ingestion_endpoint()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.tests_passed}/{self.tests_run}")
        
        if self.failed_tests:
            print(f"❌ Failed Tests:")
            for failed_test in self.failed_tests:
                print(f"   • {failed_test}")
        
        # Database status summary
        if health_status:
            print(f"\n🗄️  Database Status:")
            print(f"   • MongoDB: {health_status.get('mongodb', 'unknown')}")
            print(f"   • Redis: {health_status.get('redis', 'unknown')}")
            print(f"   • Overall: {health_status.get('status', 'unknown')}")
        
        print("\n🎯 Key Findings:")
        if self.tests_passed == self.tests_run:
            print("   • All API endpoints are working correctly")
            print("   • Pydantic v2 compatibility is working")
            print("   • Server is ready for Railway deployment")
        else:
            print("   • Some tests failed - check details above")
            if health_status.get('redis') == 'disconnected':
                print("   • Redis is disconnected but app should still work")
        
        return 0 if self.tests_passed == self.tests_run else 1

def main():
    """Main test runner"""
    tester = NVIDIADocsMCPTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())