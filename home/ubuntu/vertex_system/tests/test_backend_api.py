"""
Backend API integration tests for Vertex Full-Stack System.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, List, Optional

# Load test configuration
with open("test_config.json", "r") as f:
    config = json.load(f)

API_URL = config["api_url"]
TEST_TIMEOUT = config["test_timeout"]

def test_health_endpoint():
    """Test the health check endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health")
        response.raise_for_status()
        data = response.json()
        
        assert "status" in data, "Health response missing status field"
        assert data["status"] == "healthy", f"Unexpected health status: {data['status']}"
        assert "timestamp" in data, "Health response missing timestamp field"
        
        print("✅ Health endpoint test passed")
        return True
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

def test_providers_endpoint():
    """Test the providers endpoint."""
    print("Testing providers endpoint...")
    try:
        response = requests.get(f"{API_URL}/providers")
        response.raise_for_status()
        providers = response.json()
        
        assert isinstance(providers, list), "Providers response is not a list"
        
        if len(providers) > 0:
            provider = providers[0]
            assert "provider_id" in provider, "Provider missing provider_id field"
            assert "name" in provider, "Provider missing name field"
            assert "capabilities" in provider, "Provider missing capabilities field"
        
        print("✅ Providers endpoint test passed")
        return True
    except Exception as e:
        print(f"❌ Providers endpoint test failed: {e}")
        return False

def test_task_creation_and_retrieval():
    """Test task creation and retrieval."""
    print("Testing task creation and retrieval...")
    try:
        # Create a test task
        task_data = {
            "description": "Test task",
            "input_data": {
                "text": "This is a test input"
            },
            "priority": "MEDIUM",
            "timeout_seconds": 30,
            "max_retries": 1
        }
        
        response = requests.post(f"{API_URL}/tasks", json=task_data)
        response.raise_for_status()
        task = response.json()
        
        assert "task_id" in task, "Task response missing task_id field"
        task_id = task["task_id"]
        
        # Wait for task to complete or timeout
        start_time = time.time()
        while time.time() - start_time < TEST_TIMEOUT:
            response = requests.get(f"{API_URL}/tasks/{task_id}")
            response.raise_for_status()
            task_status = response.json()
            
            if task_status["status"] in ["COMPLETED", "FAILED"]:
                break
                
            time.sleep(1)
        
        assert "status" in task_status, "Task status response missing status field"
        print(f"Task status: {task_status['status']}")
        
        print("✅ Task creation and retrieval test passed")
        return True
    except Exception as e:
        print(f"❌ Task creation and retrieval test failed: {e}")
        return False

def test_batch_creation_and_retrieval():
    """Test batch creation and retrieval."""
    print("Testing batch creation and retrieval...")
    try:
        # Create a test batch
        batch_data = {
            "name": "Test Batch",
            "description": "Test batch description",
            "tasks": [
                {
                    "description": "Test task 1",
                    "input_data": {
                        "text": "This is test input 1"
                    },
                    "priority": "MEDIUM",
                    "timeout_seconds": 30,
                    "max_retries": 1
                },
                {
                    "description": "Test task 2",
                    "input_data": {
                        "text": "This is test input 2"
                    },
                    "priority": "MEDIUM",
                    "timeout_seconds": 30,
                    "max_retries": 1
                }
            ],
            "batch_config": {
                "max_concurrent_tasks": 2,
                "stop_on_first_failure": False
            }
        }
        
        response = requests.post(f"{API_URL}/batches", json=batch_data)
        
        # If feature is not enabled, this is expected to fail
        if response.status_code == 403:
            print("Batch feature is not enabled, skipping test")
            return True
            
        response.raise_for_status()
        batch = response.json()
        
        assert "batch_id" in batch, "Batch response missing batch_id field"
        batch_id = batch["batch_id"]
        
        # Wait for batch to complete or timeout
        start_time = time.time()
        while time.time() - start_time < TEST_TIMEOUT:
            response = requests.get(f"{API_URL}/batches/{batch_id}")
            response.raise_for_status()
            batch_status = response.json()
            
            if batch_status["status"] in ["COMPLETED", "FAILED"]:
                break
                
            time.sleep(1)
        
        assert "status" in batch_status, "Batch status response missing status field"
        print(f"Batch status: {batch_status['status']}")
        
        print("✅ Batch creation and retrieval test passed")
        return True
    except Exception as e:
        print(f"❌ Batch creation and retrieval test failed: {e}")
        return False

def test_knowledge_query():
    """Test knowledge query endpoint."""
    print("Testing knowledge query...")
    try:
        # Create a test query
        query_data = {
            "query": "test",
            "max_results": 10
        }
        
        response = requests.post(f"{API_URL}/knowledge/query", json=query_data)
        
        # If feature is not enabled, this is expected to fail
        if response.status_code == 403:
            print("Knowledge graph feature is not enabled, skipping test")
            return True
            
        response.raise_for_status()
        results = response.json()
        
        assert "entities" in results, "Query response missing entities field"
        assert "relations" in results, "Query response missing relations field"
        
        print("✅ Knowledge query test passed")
        return True
    except Exception as e:
        print(f"❌ Knowledge query test failed: {e}")
        return False

def run_all_tests():
    """Run all integration tests."""
    tests = [
        test_health_endpoint,
        test_providers_endpoint,
        test_task_creation_and_retrieval,
        test_batch_creation_and_retrieval,
        test_knowledge_query
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()  # Add a blank line between tests
    
    # Print summary
    print("Test Summary:")
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {results.count(True)}")
    print(f"Failed: {results.count(False)}")
    
    # Return exit code based on test results
    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
