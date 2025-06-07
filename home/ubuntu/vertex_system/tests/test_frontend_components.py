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
