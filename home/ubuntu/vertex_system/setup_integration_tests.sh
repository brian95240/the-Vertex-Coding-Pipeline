#!/bin/bash

# Integration test script for Vertex Full-Stack System
# This script tests the integration between frontend and backend components

echo "Starting Vertex Full-Stack System integration tests..."

# Create test directory
TEST_DIR="/home/ubuntu/vertex_system/tests"
mkdir -p $TEST_DIR

# Create test configuration
cat > $TEST_DIR/test_config.json << EOL
{
  "api_url": "http://localhost:8000",
  "test_timeout": 30,
  "providers": [
    {
      "id": "test_provider",
      "name": "Test Provider",
      "capabilities": ["text_generation", "embeddings"]
    }
  ]
}
EOL

# Create Python test script for backend API
cat > $TEST_DIR/test_backend_api.py << EOL
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
EOL

# Create Python test script for frontend components
cat > $TEST_DIR/test_frontend_components.py << EOL
"""
Frontend component tests for Vertex Full-Stack System.
"""

import os
import json
import sys
from typing import Dict, Any, List, Optional

def test_frontend_structure():
    """Test the frontend directory structure."""
    print("Testing frontend directory structure...")
    
    required_dirs = [
        "src",
        "src/components",
        "src/views",
        "src/router",
        "src/store",
        "src/services",
        "src/assets"
    ]
    
    required_files = [
        "src/main.js",
        "src/App.vue",
        "src/router/index.js",
        "src/views/DashboardView.vue",
        "src/views/TasksView.vue",
        "src/views/BatchesView.vue",
        "src/views/ProvidersView.vue",
        "src/views/KnowledgeView.vue",
        "src/views/SystemView.vue",
        "src/views/SettingsView.vue",
        "src/views/NotFoundView.vue"
    ]
    
    # Check required directories
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = os.path.join("/home/ubuntu/vertex_system/frontend", dir_path)
        if not os.path.isdir(full_path):
            missing_dirs.append(dir_path)
    
    # Check required files
    missing_files = []
    for file_path in required_files:
        full_path = os.path.join("/home/ubuntu/vertex_system/frontend", file_path)
        if not os.path.isfile(full_path):
            missing_files.append(file_path)
    
    if missing_dirs:
        print(f"❌ Missing directories: {', '.join(missing_dirs)}")
        return False
        
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ Frontend directory structure test passed")
    return True

def test_package_json():
    """Test the package.json file."""
    print("Testing package.json...")
    
    try:
        with open("/home/ubuntu/vertex_system/frontend/package.json", "r") as f:
            package_data = json.load(f)
        
        required_fields = ["name", "version", "main"]
        missing_fields = []
        
        for field in required_fields:
            if field not in package_data:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing fields in package.json: {', '.join(missing_fields)}")
            return False
        
        print("✅ package.json test passed")
        return True
    except Exception as e:
        print(f"❌ package.json test failed: {e}")
        return False

def test_vue_components():
    """Test Vue components for required elements."""
    print("Testing Vue components...")
    
    components_to_check = [
        {
            "file": "/home/ubuntu/vertex_system/frontend/src/App.vue",
            "required_elements": ["<template", "<script", "<style", "router-view"]
        },
        {
            "file": "/home/ubuntu/vertex_system/frontend/src/views/DashboardView.vue",
            "required_elements": ["<template", "<script", "<style", "dashboard"]
        },
        {
            "file": "/home/ubuntu/vertex_system/frontend/src/views/TasksView.vue",
            "required_elements": ["<template", "<script", "<style", "task"]
        }
    ]
    
    all_passed = True
    
    for component in components_to_check:
        file_path = component["file"]
        required_elements = component["required_elements"]
        
        try:
            with open(file_path, "r") as f:
                content = f.read()
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"❌ Missing elements in {os.path.basename(file_path)}: {', '.join(missing_elements)}")
                all_passed = False
            else:
                print(f"✅ {os.path.basename(file_path)} test passed")
        except Exception as e:
            print(f"❌ {os.path.basename(file_path)} test failed: {e}")
            all_passed = False
    
    return all_passed

def run_all_tests():
    """Run all frontend component tests."""
    tests = [
        test_frontend_structure,
        test_package_json,
        test_vue_components
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
EOL

# Create integration test script
cat > $TEST_DIR/run_integration_tests.sh << EOL
#!/bin/bash

# Run integration tests for Vertex Full-Stack System

# Set up environment
cd /home/ubuntu/vertex_system

# Start backend server in background
echo "Starting backend server..."
cd /home/ubuntu/vertex_system
python3 main.py &
BACKEND_PID=\$!

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Run backend API tests
echo "Running backend API tests..."
cd /home/ubuntu/vertex_system/tests
python3 test_backend_api.py
BACKEND_TEST_RESULT=\$?

# Run frontend component tests
echo "Running frontend component tests..."
cd /home/ubuntu/vertex_system/tests
python3 test_frontend_components.py
FRONTEND_TEST_RESULT=\$?

# Stop backend server
echo "Stopping backend server..."
kill \$BACKEND_PID

# Print overall results
echo ""
echo "Integration Test Results:"
echo "------------------------"
echo "Backend API Tests: \$([ \$BACKEND_TEST_RESULT -eq 0 ] && echo 'PASSED' || echo 'FAILED')"
echo "Frontend Component Tests: \$([ \$FRONTEND_TEST_RESULT -eq 0 ] && echo 'PASSED' || echo 'FAILED')"

# Return overall result
if [ \$BACKEND_TEST_RESULT -eq 0 ] && [ \$FRONTEND_TEST_RESULT -eq 0 ]; then
  echo "All integration tests PASSED"
  exit 0
else
  echo "Some integration tests FAILED"
  exit 1
fi
EOL

# Make the test script executable
chmod +x $TEST_DIR/run_integration_tests.sh

echo "Integration test scripts created successfully."
echo "To run the tests, execute: $TEST_DIR/run_integration_tests.sh"
