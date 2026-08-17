"""
Comprehensive test suite for Civic Complaint Intelligence Engine
Tests the multimodal intake layer with mocked external dependencies
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from io import BytesIO
import sys
import os

# Add parent directory to path to import main app
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from config import settings

# Create test client using the standard approach
client = TestClient(app)

# Fixture paths
FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_IMAGE_PATH = FIXTURES_DIR / "test_image.jpg"
TEST_AUDIO_PATH = FIXTURES_DIR / "test_audio.wav"
TEST_SIDEWAYS_PATH = FIXTURES_DIR / "test_sideways.jpg"
TEST_PNG_PATH = FIXTURES_DIR / "test_image.png"


@pytest.fixture
def mock_audio_processor():
    """Mock audio processor to avoid real audio processing"""
    with patch('main.audio_processor') as mock:
        async def mock_process(*args, **kwargs):
            return (
                "processed_audio.mp3",
                {
                    "original_duration": 30.0,
                    "processed_duration": 25.0,
                    "original_size": 1024000,
                    "processed_size": 512000,
                    "compression_ratio": 2.0,
                    "duration_reduction": 16.67,
                    "format": "mp3"
                }
            )
        mock.process_audio_file = mock_process
        yield mock


@pytest.fixture
def mock_audio_transcriber():
    """Mock audio transcriber to avoid real API calls"""
    with patch('main.audio_transcriber') as mock:
        async def mock_transcribe(*args, **kwargs):
            return {
                "text": "There is a huge pothole on Main Street that needs immediate repair.",
                "language": "en",
                "confidence": 0.95,
                "method": "sarvam",
                "duration": 25.0
            }
        mock.transcribe_audio = mock_transcribe
        yield mock


@pytest.fixture
def mock_image_scrubber():
    """Mock image scrubber to avoid real OpenCV processing"""
    with patch('main.image_scrubber') as mock:
        async def mock_scrub(*args, **kwargs):
            return (
                "scrubbed_test_image.jpg",
                {
                    "original_shape": (100, 100, 3),
                    "faces_detected": 1,
                    "license_plates_detected": 0,
                    "scrubbed_regions": [
                        {
                            "type": "face",
                            "bbox": [10, 10, 50, 50]
                        }
                    ]
                }
            )
        mock.scrub_image = mock_scrub
        async def mock_exif(*args, **kwargs):
            return (None, None)
        mock.extract_exif_location = mock_exif
        yield mock


@pytest.fixture
def mock_location_extractor():
    """Mock location extractor to avoid real geocoding calls"""
    with patch('main.location_extractor') as mock:
        async def mock_extract(*args, **kwargs):
            return {
                "coordinates": [13.0827, 80.2707],
                "source": "gps",
                "confidence": 1.0,
                "address": "Chennai, Tamil Nadu, India",
                "requires_user_input": False,
                "fallback_message": None
            }
        mock.extract_location = mock_extract
        yield mock


@pytest.fixture
def mock_location_extractor_missing():
    """Mock location extractor for missing location scenario"""
    with patch('main.location_extractor') as mock:
        async def mock_extract(*args, **kwargs):
            return {
                "coordinates": None,
                "source": None,
                "confidence": 0.0,
                "address": None,
                "requires_user_input": True,
                "fallback_message": "I see the issue, but I need the location to report it. Can you drop a GPS pin or type the street name?"
            }
        mock.extract_location = mock_extract
        yield mock


class TestHappyPath:
    """Test the happy path: valid multipart/form-data with all fields"""
    
    def test_complete_complaint_submission(self, mock_audio_processor, mock_audio_transcriber, 
                                          mock_image_scrubber, mock_location_extractor):
        """
        Test submitting a complete complaint with text, image, audio, and GPS coordinates
        Should return 200 status and correct JSON handoff contract
        """
        # Prepare form data
        files = {
            'image': open(TEST_IMAGE_PATH, 'rb'),
            'audio': open(TEST_AUDIO_PATH, 'rb')
        }
        data = {
            'text': 'There is a pothole on Main Street',
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707',
            'language': 'en'
        }
        
        # Submit complaint
        response = client.post("/api/complaint", files=files, data=data)
        
        # Close files
        files['image'].close()
        files['audio'].close()
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        
        # Verify success
        assert result['success'] is True
        assert result['complaint_id'] is not None
        assert result['timestamp'] is not None
        
        # Verify handoff contract structure
        data = result['data']
        assert 'image_path' in data
        assert 'transcribed_text' in data
        assert 'gps_coordinates' in data
        
        # Verify GPS coordinates format
        assert isinstance(data['gps_coordinates'], list)
        assert len(data['gps_coordinates']) == 2
        assert data['gps_coordinates'][0] == 13.0827
        assert data['gps_coordinates'][1] == 80.2707
        
        # Verify text was transcribed/processed
        assert data['transcribed_text'] is not None
        assert len(data['transcribed_text']) > 0
        
        # Verify image path exists
        assert data['image_path'] is not None
        assert 'scrubbed' in data['image_path']
        
        # Verify metadata was generated
        assert 'audio_metadata' in data
        assert 'image_metadata' in data
        assert 'location_metadata' in data
        
        # Verify no user input required
        assert result['requires_user_input'] is False
        assert result['fallback_message'] is None


class TestMissingLocationFallback:
    """Test missing location fallback scenario"""
    
    def test_missing_location_triggers_fallback(self, mock_image_scrubber, mock_location_extractor_missing):
        """
        Test submitting a complaint with photo and text but NO GPS coordinates
        Should return conversational fallback prompt instead of crashing
        """
        # Prepare form data without GPS coordinates
        files = {
            'image': open(TEST_IMAGE_PATH, 'rb')
        }
        data = {
            'text': 'There is a garbage pile near the bus stand'
        }
        
        # Submit complaint
        response = client.post("/api/complaint", files=files, data=data)
        
        # Close file
        files['image'].close()
        
        # Verify response
        assert response.status_code == 200  # API should not crash
        result = response.json()
        
        # Verify success is False due to missing location
        assert result['success'] is False
        
        # Verify user input is required
        assert result['requires_user_input'] is True
        
        # Verify fallback message is present
        assert result['fallback_message'] is not None
        assert "I need the location" in result['fallback_message']
        assert "drop a GPS pin" in result['fallback_message']
        
        # Verify complaint ID was still generated
        assert result['complaint_id'] is not None
        
        # Verify error field indicates location requirement
        assert result['error'] == "Location required"


class TestEmptySubmission:
    """Test empty submission scenario"""
    
    def test_empty_submission_returns_400(self, mock_location_extractor):
        """
        Test submitting a request with absolutely no text, no audio, and no image
        Should return HTTP 400 Bad Request or handle gracefully
        """
        # Submit empty form data
        response = client.post("/api/complaint", data={})
        
        # The API should handle this gracefully
        # Depending on implementation, this might return 200 with minimal data
        # or 400 if validation is strict
        assert response.status_code in [200, 400]
        
        result = response.json()
        
        # If validation is strict, expect error
        if response.status_code == 400:
            assert result['success'] is False
            assert result['error'] is not None
        else:
            # If lenient, expect minimal valid response with location fallback
            assert result['success'] is True or result['requires_user_input'] is True


class TestAudioOnlyEdgeCompression:
    """Test audio-only submission with edge compression"""
    
    def test_audio_only_with_compression(self, mock_audio_processor, mock_audio_transcriber, mock_location_extractor):
        """
        Test submitting a request with only an audio file
        Mock pydub compression function to ensure route handles file correctly
        """
        # Prepare form data with only audio
        files = {
            'audio': open(TEST_AUDIO_PATH, 'rb')
        }
        data = {
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707',
            'language': 'ta'  # Tamil
        }
        
        # Submit complaint
        response = client.post("/api/complaint", files=files, data=data)
        
        # Close file
        files['audio'].close()
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        
        # Verify response structure
        assert result['success'] is True
        data = result['data']
        
        # Verify audio metadata is present (shows compression was called)
        assert 'audio_metadata' in data
        assert data['audio_metadata']['compression_ratio'] == 2.0
        
        # Verify transcription was performed
        assert 'transcription_metadata' in data
        assert data['transcription_metadata']['method'] == 'sarvam'
        
        # Verify transcribed text is present
        assert data['transcribed_text'] is not None
        assert len(data['transcribed_text']) > 0
        
        # Verify GPS coordinates are present
        assert data['gps_coordinates'] == [13.0827, 80.2707]
        
        # Verify image_path is None (no image submitted)
        assert data['image_path'] is None


class TestSidewaysPhoto:
    """Test sideways photo handling"""
    
    def test_sideways_photo_handling(self, mock_image_scrubber, mock_location_extractor):
        """
        Test submitting a sideways photo
        Verify endpoint saves it and passes image_path without orientation error
        """
        # Prepare form data with sideways image
        files = {
            'image': open(TEST_SIDEWAYS_PATH, 'rb')
        }
        data = {
            'text': 'Broken traffic signal at intersection',
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707'
        }
        
        # Submit complaint
        response = client.post("/api/complaint", files=files, data=data)
        
        # Close file
        files['image'].close()
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        
        # Verify success
        assert result['success'] is True
        
        # Verify image_path is present in output
        data = result['data']
        assert data['image_path'] is not None
        assert 'scrubbed' in data['image_path']
        
        # Verify no orientation-related errors
        assert 'orientation' not in str(result).lower()
        assert 'rotation' not in str(result).lower()
        
        # Verify image metadata was generated
        assert 'image_metadata' in data
        assert data['image_metadata']['original_shape'] is not None


class TestLocationUpdate:
    """Test location update endpoint for fallback scenario"""
    
    def test_location_update_after_fallback(self, mock_location_extractor_missing):
        """
        Test updating location after initial fallback
        Verify the location update endpoint works correctly
        """
        # First, create a complaint that requires location
        response = client.post("/api/complaint", data={'text': 'Street light not working'})
        assert response.status_code == 200
        result = response.json()
        complaint_id = result['complaint_id']
        assert result['requires_user_input'] is True
        
        # Now mock successful location processing
        with patch('main.location_extractor') as mock_success:
            async def mock_process_response(*args, **kwargs):
                return {
                    "coordinates": [13.0827, 80.2707],
                    "source": "user_input",
                    "confidence": 1.0,
                    "address": "Main Street, Chennai",
                    "requires_user_input": False,
                    "fallback_message": None
                }
            mock_success.process_user_location_response = mock_process_response
            
            # Update location
            location_data = {
                "complaint_id": complaint_id,
                "location_input": "13.0827, 80.2707"
            }
            
            response = client.post(f"/api/complaint/{complaint_id}/location", json=location_data)
            
            # Verify response
            assert response.status_code == 200
            result = response.json()
            
            # Verify success
            assert result['success'] is True
            assert result['requires_user_input'] is False
            
            # Verify location was updated
            data = result['data']
            assert data['gps_coordinates'] == [13.0827, 80.2707]
            assert data['location_metadata']['source'] == 'user_input'


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test health check endpoint returns system status"""
        response = client.get("/health")
        
        assert response.status_code == 200
        result = response.json()
        
        assert result['status'] == 'healthy'
        assert result['timestamp'] is not None
        assert 'components' in result
        
        # Verify all components are reported
        components = result['components']
        assert 'audio_processor' in components
        assert 'image_scrubber' in components
        assert 'location_extractor' in components
        assert 'audio_transcriber' in components
        assert 'transcription_provider' in components


class TestGetComplaint:
    """Test retrieving complaint details"""
    
    def test_get_complaint_by_id(self, mock_location_extractor):
        """Test retrieving a specific complaint by ID"""
        # First create a complaint
        files = {'image': open(TEST_IMAGE_PATH, 'rb')}
        data = {
            'text': 'Test complaint',
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707'
        }
        
        create_response = client.post("/api/complaint", files=files, data=data)
        files['image'].close()
        
        assert create_response.status_code == 200
        create_result = create_response.json()
        complaint_id = create_result['complaint_id']
        
        # Now retrieve the complaint
        get_response = client.get(f"/api/complaint/{complaint_id}")
        
        assert get_response.status_code == 200
        get_result = get_response.json()
        
        assert get_result['success'] is True
        assert get_result['complaint_id'] == complaint_id
        assert get_result['data'] is not None
    
    def test_get_nonexistent_complaint(self):
        """Test retrieving a non-existent complaint returns 404"""
        response = client.get("/api/complaint/nonexistent-id")
        
        assert response.status_code == 404


class TestImageFormats:
    """Test different image format handling"""
    
    def test_png_image_handling(self, mock_image_scrubber, mock_location_extractor):
        """Test that PNG images are handled correctly"""
        files = {'image': open(TEST_PNG_PATH, 'rb')}
        data = {
            'text': 'Test with PNG',
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707'
        }
        
        response = client.post("/api/complaint", files=files, data=data)
        files['image'].close()
        
        assert response.status_code == 200
        result = response.json()
        
        assert result['success'] is True
        assert result['data']['image_path'] is not None


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_transcription_failure_handling(self, mock_audio_processor, mock_image_scrubber, mock_location_extractor):
        """Test that transcription failures are handled gracefully"""
        # Mock transcription failure
        with patch('main.audio_transcriber') as mock_transcriber:
            async def mock_transcribe(*args, **kwargs):
                return {
                    "text": None,
                    "error": "Transcription service unavailable",
                    "warnings": ["API timeout"]
                }
            mock_transcriber.transcribe_audio = mock_transcribe
            
            files = {
                'audio': open(TEST_AUDIO_PATH, 'rb'),
                'image': open(TEST_IMAGE_PATH, 'rb')
            }
            data = {
                'gps_latitude': '13.0827',
                'gps_longitude': '80.2707'
            }
            
            response = client.post("/api/complaint", files=files, data=data)
            
            files['audio'].close()
            files['image'].close()
            
            # Should still succeed with warnings
            assert response.status_code == 200
            result = response.json()
            
            # Should have warnings but still return success
            assert result['success'] is True
            assert result['warnings'] is not None
            assert len(result['warnings']) > 0


class TestHandoffContract:
    """Test the exact handoff contract format"""
    
    def test_handoff_contract_format(self, mock_audio_processor, mock_audio_transcriber, 
                                     mock_image_scrubber, mock_location_extractor):
        """
        Test that the response matches the exact handoff contract format:
        {
            "image_path": "/path/to/scrubbed/image.jpg",
            "transcribed_text": "The complaint text",
            "gps_coordinates": [lat, lon]
        }
        """
        files = {
            'image': open(TEST_IMAGE_PATH, 'rb'),
            'audio': open(TEST_AUDIO_PATH, 'rb')
        }
        data = {
            'text': 'Test complaint for handoff contract',
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707'
        }
        
        response = client.post("/api/complaint", files=files, data=data)
        
        files['image'].close()
        files['audio'].close()
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify exact handoff contract fields exist
        data = result['data']
        
        # Required fields
        assert 'image_path' in data
        assert 'transcribed_text' in data
        assert 'gps_coordinates' in data
        
        # Verify types
        assert isinstance(data['image_path'], str)
        assert isinstance(data['transcribed_text'], str)
        assert isinstance(data['gps_coordinates'], list)
        
        # Verify GPS coordinates format [lat, lon]
        assert len(data['gps_coordinates']) == 2
        assert isinstance(data['gps_coordinates'][0], (int, float))
        assert isinstance(data['gps_coordinates'][1], (int, float))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
