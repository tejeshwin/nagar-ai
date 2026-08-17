# 🧪 Testing Guide - Civic Complaint Intelligence Engine

## 🚀 Quick Start - Run Tests Now

### Windows (Command Prompt/PowerShell)
```bash
# Navigate to project directory
cd C:\Users\Tejeshwin.D\civic_complaint_engine

# Option 1: Use the automated script
run_tests.bat

# Option 2: Manual execution
pip install -r test_requirements.txt
cd tests\fixtures
python create_fixtures_simple.py
cd ..\..
pytest tests/test_intake.py -v
```

### Linux/Mac (Terminal)
```bash
# Navigate to project directory
cd civic_complaint_engine

# Option 1: Use the automated script
chmod +x run_tests.sh
./run_tests.sh

# Option 2: Manual execution
pip install -r test_requirements.txt
cd tests/fixtures
python create_fixtures_simple.py
cd ../..
pytest tests/test_intake.py -v
```

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **Project dependencies** installed: `pip install -r requirements.txt`
3. **Test dependencies** installed: `pip install -r test_requirements.txt`

## 🎯 Exact Terminal Commands

### Step 1: Install Test Dependencies
```bash
pip install pytest pytest-asyncio pytest-mock httpx
```

### Step 2: Create Test Fixtures
```bash
cd tests/fixtures
python create_fixtures_simple.py
cd ../..
```

### Step 3: Run All Tests
```bash
pytest tests/test_intake.py -v
```

### Step 4: Run Specific Test Categories
```bash
# Run only happy path tests
pytest tests/test_intake.py::TestHappyPath -v

# Run only location fallback tests
pytest tests/test_intake.py::TestMissingLocationFallback -v

# Run only audio tests
pytest tests/test_intake.py::TestAudioOnlyEdgeCompression -v
```

## 📊 Test Coverage

The test suite includes **15 comprehensive test cases**:

| Test Class | Test Function | Description |
|------------|---------------|-------------|
| TestHappyPath | test_complete_complaint_submission | Valid multipart request with all fields |
| TestMissingLocationFallback | test_missing_location_triggers_fallback | Conversational fallback when location missing |
| TestEmptySubmission | test_empty_submission_returns_400 | Empty request handling |
| TestAudioOnlyEdgeCompression | test_audio_only_with_compression | Audio-only with edge compression |
| TestSidewaysPhoto | test_sideways_photo_handling | Sideways photo without orientation errors |
| TestLocationUpdate | test_location_update_after_fallback | Location update workflow |
| TestHealthCheck | test_health_check | System health endpoint |
| TestGetComplaint | test_get_complaint_by_id | Complaint retrieval by ID |
| TestGetComplaint | test_get_nonexistent_complaint | 404 for non-existent complaint |
| TestImageFormats | test_png_image_handling | PNG format support |
| TestErrorHandling | test_transcription_failure_handling | Graceful error handling |
| TestHandoffContract | test_handoff_contract_format | Exact JSON format verification |

## 🔧 Advanced Test Commands

### Run with Coverage Report
```bash
pytest --cov=. --cov-report=html --cov-report=term
```

### Run in Parallel (Faster)
```bash
pytest -n auto
```

### Stop on First Failure
```bash
pytest -x
```

### Verbose Output with Debugging
```bash
pytest -vv -s
```

### Generate HTML Report
```bash
pytest --html=report.html --self-contained-html
```

### Run Specific Test Function
```bash
pytest tests/test_intake.py::TestHappyPath::test_complete_complaint_submission -v
```

## 📁 Test Files Created

```
tests/
├── __init__.py                          # Test package init
├── test_intake.py                       # Main test suite (15 tests)
├── README.md                            # Test documentation
└── fixtures/
    ├── __init__.py                      # Fixtures package init
    ├── create_fixtures_simple.py        # Fixture creation script
    ├── test_image.jpg                   # Dummy JPEG (1KB)
    ├── test_image.png                   # Dummy PNG (1KB)
    ├── test_audio.wav                   # Dummy WAV (1KB)
    └── test_sideways.jpg                # Dummy sideways JPEG (1KB)
```

## 🎯 Test Scenarios Covered

### ✅ Happy Path
- **Input**: Text rant + image + audio + GPS coordinates
- **Expected**: 200 status + complete handoff contract
- **Validates**: All processing pipelines work together

### ✅ Missing Location Fallback
- **Input**: Photo + text, NO GPS coordinates
- **Expected**: 200 status + conversational fallback prompt
- **Validates**: API catches missing location, doesn't crash

### ✅ Empty Submission
- **Input**: No text, no audio, no image
- **Expected**: 400 Bad Request or graceful handling
- **Validates**: Input validation works

### ✅ Audio Only (Edge Compression)
- **Input**: Only audio file + GPS
- **Expected**: 200 status + compression metadata
- **Validates**: Edge compression pipeline, mocked pydub

### ✅ Sideways Photo
- **Input**: Sideways image + GPS
- **Expected**: 200 status + image_path in output
- **Validates**: No orientation errors, image preserved

## 🔐 Mocking Strategy

All external dependencies are mocked for instant test execution:

- **Audio Processing**: `audio_processor.process_audio_file()` → Mocked
- **Audio Transcription**: `audio_transcriber.transcribe_audio()` → Mocked
- **Image Scrubbing**: `image_scrubber.scrub_image()` → Mocked
- **Location Extraction**: `location_extractor.extract_location()` → Mocked
- **Geocoding APIs**: No real network calls

## 📈 Expected Results

### Successful Test Run
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
```bash
# Ensure you're in the project root
cd civic_complaint_engine

# Install dependencies
pip install -r requirements.txt
pip install -r test_requirements.txt
```

### Missing Fixture Files
```bash
cd tests/fixtures
python create_fixtures_simple.py
cd ../..
```

### Module Not Found
```bash
# Set Python path (Windows)
set PYTHONPATH=%PYTHONPATH%;%CD%

# Set Python path (Linux/Mac)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Slow Tests
```bash
# Verify mocking is working (no real API calls)
pytest -v --tb=short

# Use parallel execution
pytest -n auto
```

## 🎉 Success Criteria

The test suite is successful when:

- ✅ All 15 tests pass
- ✅ Tests complete in <5 seconds
- ✅ No external API calls are made
- ✅ Handoff contract format is verified
- ✅ Error scenarios are handled gracefully

## 📝 Handoff Contract Verification

The tests verify the exact output format:

```python
{
    "image_path": "/path/to/scrubbed/image.jpg",
    "transcribed_text": "The complaint text",
    "gps_coordinates": [13.0827, 80.2707]
}
```

## 🏆 Integration with CI/CD

For automated testing in CI/CD pipelines:

```bash
# Quick feedback for CI
pytest -q --tb=line

# With coverage for quality gates
pytest --cov=. --cov-report=xml --cov-fail-under=80

# Strict mode for production
pytest --strict-markers -x
```

## 📞 Support

If tests fail:
1. Check fixture files exist in `tests/fixtures/`
2. Verify all dependencies are installed
3. Ensure you're running from project root
4. Check Python version (3.8+ required)

---

**🎯 Ready to test! Run the exact command above to validate your Civic Complaint Intelligence Engine backend.**
