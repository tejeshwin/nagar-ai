# 🧪 Test Suite Documentation

## Overview
Comprehensive test suite for the Civic Complaint Intelligence Engine backend using pytest and FastAPI's TestClient. All external dependencies (API calls, heavy processing) are mocked for fast, reliable testing.

## 📁 Test Structure

```
tests/
├── __init__.py
├── test_intake.py              # Main test suite
├── fixtures/
│   ├── __init__.py
│   ├── create_fixtures_simple.py  # Script to create dummy files
│   ├── test_image.jpg          # Dummy JPEG image
│   ├── test_image.png          # Dummy PNG image
│   ├── test_audio.wav          # Dummy WAV audio
│   └── test_sideways.jpg       # Dummy sideways image
```

## 🚀 Quick Start

### 1. Install Test Dependencies

```bash
# Navigate to project directory
cd civic_complaint_engine

# Install test dependencies
pip install -r test_requirements.txt

# (Or if you already have main requirements installed)
pip install pytest pytest-asyncio pytest-mock httpx
```

### 2. Create Test Fixtures

```bash
# Create dummy test files
cd tests/fixtures
python create_fixtures_simple.py
cd ../..
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_intake.py

# Run specific test class
pytest tests/test_intake.py::TestHappyPath

# Run specific test function
pytest tests/test_intake.py::TestHappyPath::test_complete_complaint_submission
```

## 🎯 Test Coverage

### Test Classes

1. **TestHappyPath** - Complete complaint submission with all fields
2. **TestMissingLocationFallback** - Location fallback scenario
3. **TestEmptySubmission** - Empty request handling
4. **TestAudioOnlyEdgeCompression** - Audio-only with compression
5. **TestSidewaysPhoto** - Sideways photo handling
6. **TestLocationUpdate** - Location update after fallback
7. **TestHealthCheck** - Health check endpoint
8. **TestGetComplaint** - Complaint retrieval
9. **TestImageFormats** - Different image format handling
10. **TestErrorHandling** - Error scenario handling
11. **TestHandoffContract** - Exact handoff contract format verification

### Key Test Scenarios

✅ **Happy Path**: Valid multipart/form-data with text, image, audio, GPS
✅ **Missing Location Fallback**: Conversational prompt when location missing
✅ **Empty Submission**: Proper handling of empty requests
✅ **Audio Only**: Edge compression with mocked pydub
✅ **Sideways Photo**: Orientation preservation without errors
✅ **Location Update**: Fallback completion workflow
✅ **Handoff Contract**: Exact JSON format verification

## 🔧 Mocking Strategy

All external dependencies are mocked to ensure fast, reliable tests:

- **Audio Processing**: Mocked `audio_processor.process_audio_file()`
- **Audio Transcription**: Mocked `audio_transcriber.transcribe_audio()`
- **Image Scrubbing**: Mocked `image_scrubber.scrub_image()`
- **Location Extraction**: Mocked `location_extractor.extract_location()`
- **Geocoding APIs**: Mocked to avoid network calls

## 📊 Test Commands

### Basic Commands

```bash
# Run all tests
pytest

# Verbose mode
pytest -v

# Show test execution time
pytest -v --durations=10

# Stop on first failure
pytest -x

# Stop on first failure and enter debugger
pytest -x --pdb
```

### Advanced Commands

```bash
# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific markers
pytest -m "not slow"

# Parallel execution (requires pytest-xdist)
pytest -n auto

# Generate HTML report
pytest --html=report.html

# Run with detailed output
pytest -vv -s
```

### Debugging Commands

```bash
# Run with print statements
pytest -s

# Run with logging
pytest --log-cli-level=DEBUG

# Run specific test with debugging
pytest tests/test_intake.py::TestHappyPath::test_complete_complaint_submission -vv -s
```

## 🧪 Fixture Files

The test suite uses minimal dummy files to avoid external dependencies:

- **test_image.jpg**: 1KB JPEG image (minimal valid format)
- **test_image.png**: 1KB PNG image (minimal valid format)
- **test_audio.wav**: 1KB WAV audio (silence, valid format)
- **test_sideways.jpg**: JPEG for testing sideways photo handling

These files are created by `create_fixtures_simple.py` and contain only valid headers/metadata - no actual image/audio content.

## 📝 Expected Output

When tests run successfully, you should see:

```
============================= test session starts =============================
platform win32 -- Python 3.x.x, pytest-7.4.3
rootdir: C:\Users\Tejeshwin.D\civic_complaint_engine
collected 15 items

tests/test_intake.py::TestHappyPath::test_complete_complaint_submission PASSED
tests/test_intake.py::TestMissingLocationFallback::test_missing_location_triggers_fallback PASSED
tests/test_intake.py::TestEmptySubmission::test_empty_submission_returns_400 PASSED
tests/test_intake.py::TestAudioOnlyEdgeCompression::test_audio_only_with_compression PASSED
tests/test_intake.py::TestSidewaysPhoto::test_sideways_photo_handling PASSED
tests/test_intake.py::TestLocationUpdate::test_location_update_after_fallback PASSED
tests/test_intake.py::TestHealthCheck::test_health_check PASSED
tests/test_intake.py::TestGetComplaint::test_get_complaint_by_id PASSED
tests/test_intake.py::TestGetComplaint::test_get_nonexistent_complaint PASSED
tests/test_intake.py::TestImageFormats::test_png_image_handling PASSED
tests/test_intake.py::TestErrorHandling::test_transcription_failure_handling PASSED
tests/test_intake.py::TestHandoffContract::test_handoff_contract_format PASSED

============================== 15 passed in 2.34s ==============================
```

## 🐛 Troubleshooting

### Import Errors

If you get import errors:
```bash
# Make sure you're in the project root
cd civic_complaint_engine

# Install main dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r test_requirements.txt
```

### Fixture Files Missing

If tests fail due to missing fixture files:
```bash
cd tests/fixtures
python create_fixtures_simple.py
cd ../..
```

### Module Not Found Errors

If you get "Module not found" errors:
```bash
# Ensure the project root is in your Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%CD%         # Windows
```

### Slow Tests

If tests are running slowly:
```bash
# Check that mocking is working (no real API calls)
pytest -v --tb=short

# Use parallel execution
pytest -n auto
```

## 🎯 Test Cases Detail

### 1. Happy Path Test
- **Input**: Text, image, audio, GPS coordinates
- **Expected**: 200 status, complete handoff contract
- **Validates**: All processing pipelines work together

### 2. Missing Location Fallback Test
- **Input**: Text, image, NO GPS coordinates
- **Expected**: 200 status, conversational fallback message
- **Validates**: API doesn't crash, prompts user for location

### 3. Empty Submission Test
- **Input**: No data at all
- **Expected**: 400 status or graceful handling
- **Validates**: Input validation works

### 4. Audio Only Test
- **Input**: Audio file + GPS
- **Expected**: 200 status, compression metadata
- **Validates**: Edge compression pipeline works

### 5. Sideways Photo Test
- **Input**: Sideways image + GPS
- **Expected**: 200 status, image_path present
- **Validates**: No orientation errors, image preserved

## 🏆 Continuous Integration

For CI/CD pipelines, use:

```bash
# Run tests with coverage
pytest --cov=. --cov-report=xml --cov-report=term

# Exit with non-zero on failure
pytest --strict-markers -x

# Fast feedback for CI
pytest -q --tb=line
```

## 📈 Coverage Goals

Aim for:
- **Line Coverage**: >80%
- **Branch Coverage**: >70%
- **Critical Paths**: 100% coverage

## 🔐 Security Testing

The test suite validates:
- Input validation (empty submissions)
- Error handling (API failures)
- Data sanitization (image scrubbing)
- Privacy protection (location fallback)

## 🎉 Summary

This test suite provides comprehensive coverage of the Civic Complaint Intelligence Engine intake layer with:
- ✅ Fast execution (mocked dependencies)
- ✅ Reliable results (no external API calls)
- ✅ Complete scenario coverage (happy path to edge cases)
- ✅ Production-ready validation (handoff contract verification)

Run the tests with confidence before deploying to production!
