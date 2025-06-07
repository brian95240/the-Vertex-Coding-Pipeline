#!/bin/bash

# Run integration tests for Vertex Full-Stack System

# Set up environment
cd /home/ubuntu/vertex_system

# Start backend server in background
echo "Starting backend server..."
cd /home/ubuntu/vertex_system
python3 main.py &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Run backend API tests
echo "Running backend API tests..."
cd /home/ubuntu/vertex_system/tests
python3 test_backend_api.py
BACKEND_TEST_RESULT=$?

# Run frontend component tests
echo "Running frontend component tests..."
cd /home/ubuntu/vertex_system/tests
python3 test_frontend_components.py
FRONTEND_TEST_RESULT=$?

# Stop backend server
echo "Stopping backend server..."
kill $BACKEND_PID

# Print overall results
echo ""
echo "Integration Test Results:"
echo "------------------------"
echo "Backend API Tests: $([ $BACKEND_TEST_RESULT -eq 0 ] && echo 'PASSED' || echo 'FAILED')"
echo "Frontend Component Tests: $([ $FRONTEND_TEST_RESULT -eq 0 ] && echo 'PASSED' || echo 'FAILED')"

# Return overall result
if [ $BACKEND_TEST_RESULT -eq 0 ] && [ $FRONTEND_TEST_RESULT -eq 0 ]; then
  echo "All integration tests PASSED"
  exit 0
else
  echo "Some integration tests FAILED"
  exit 1
fi
