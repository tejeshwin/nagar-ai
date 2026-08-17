@echo off
REM Test execution script for Civic Complaint Intelligence Engine
REM Windows batch script to run the test suite

echo ========================================
echo Civic Complaint Intelligence Engine
echo Test Suite Execution
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    echo Installing dependencies...
    pip install -r requirements.txt
    pip install -r test_requirements.txt
) else (
    echo Activating virtual environment...
    call venv\Scripts\activate
)

REM Create test fixtures if they don't exist
if not exist "tests\fixtures\test_image.jpg" (
    echo Creating test fixtures...
    cd tests\fixtures
    python create_fixtures_simple.py
    cd ..\..
)

REM Run tests
echo.
echo Running test suite...
echo.
pytest tests/test_intake.py -v

echo.
echo ========================================
echo Test execution completed
echo ========================================
pause