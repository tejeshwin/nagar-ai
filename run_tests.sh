#!/bin/bash
# Test execution script for Civic Complaint Intelligence Engine
# Shell script for Linux/Mac to run the test suite

echo "========================================"
echo "Civic Complaint Intelligence Engine"
echo "Test Suite Execution"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
    pip install -r test_requirements.txt
else
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Create test fixtures if they don't exist
if [ ! -f "tests/fixtures/test_image.jpg" ]; then
    echo "Creating test fixtures..."
    cd tests/fixtures
    python create_fixtures_simple.py
    cd ../..
fi

# Run tests
echo ""
echo "Running test suite..."
echo ""
pytest tests/test_intake.py -v

echo ""
echo "========================================"
echo "Test execution completed"
echo "========================================"