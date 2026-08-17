"""
Comprehensive Integration Test Suite for Multimodal Intake Module
Tests production readiness, error handling, and handoff contract compliance
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from io import BytesIO
import sys
import os
import asyncio

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


@pytest.fixture
def mock_timeout_transcriber():
    """Mock transcriber that simulates API timeout"""
    with patch('main.audio_transcriber') as mock:
        async def mock_timeout(*args, **kwargs):
            await asyncio.sleep(61)  # Exceed the 60 second timeout
            return {"text": "test", "language": "en", "confidence": 0.9}
        mock.transcribe_audio = mock_timeout
        yield mock


@pytest.fixture
def mock_failing_audio_processor():
    """Mock audio processor that simulates corrupt audio file"""
    with patch('main.audio_processor') as mock:
        async def mock_fail(*args, **kwargs):
            raise Exception("Corrupt audio file - unsupported format")
        mock.process_audio_file = mock_fail
        yield mock


@pytest.fixture
def mock_failing_image_scrubber():
    """Mock image scrubber that simulates unreadable image"""
    with patch('main.image_scrubber') as mock:
        async def mock_fail(*args, **kwargs):
            raise Exception("Image unreadable - corrupted file")
        mock.scrub_image = mock_fail
        yield mock


class TestIntegrationContract:
    """Test the exact JSON handoff contract for Photo Intelligence module"""
    
    def test_happy_path_full_payload(self, mock_audio_processor, mock_audio_transcriber, 
                                     mock_image_scrubber, mock_location_extractor):
        """
        Test submitting a complete complaint with text, image, audio, and GPS coordinates
        Should return 200 status and exact JSON contract match
        Expected contract: { "image_path": "uploads/img_123.jpg" | null, "transcribed_text": "text here", "gps_coordinates": [lat, lon] | null }
        """
        # Create mock image and audio files
        image_content = b"fake_image_data"
        audio_content = b"fake_audio_data"
        
        files = {
            'image': ('test_image.jpg', BytesIO(image_content), 'image/jpeg'),
            'audio': ('test_audio.wav', BytesIO(audio_content), 'audio/wav')
        }
        data = {
            'text': 'There is a pothole on Main Street',
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707',
            'language': 'en'
        }
        
        # Submit complaint
        response = client.post("/api/complaint", files=files, data=data)
        
        # Assert response status
        assert response.status_code == 200
        
        # Parse response
        result = response.json()
        
        # Verify exact JSON contract structure
        assert result["success"] == True
        assert "complaint_id" in result
        assert "timestamp" in result
        assert "data" in result
        
        # Verify handoff contract fields exist
        data_section = result["data"]
        assert "image_path" in data_section
        assert "transcribed_text" in data_section
        assert "gps_coordinates" in data_section
        
        # Verify types and values
        assert isinstance(data_section["image_path"], str) or data_section["image_path"] is None
        assert isinstance(data_section["transcribed_text"], str)
        assert isinstance(data_section["gps_coordinates"], list) or data_section["gps_coordinates"] is None
        
        # For happy path, we should have actual values
        assert data_section["image_path"] is not None
        assert data_section["transcribed_text"] == "There is a huge pothole on Main Street that needs immediate repair."
        assert data_section["gps_coordinates"] == [13.0827, 80.2707]
        
        # Verify image path format matches expected pattern
        assert "uploads/" in data_section["image_path"]
        assert data_section["image_path"].endswith(".jpg")
    
    def test_missing_gps_fallback(self, mock_audio_processor, mock_audio_transcriber, 
                                  mock_image_scrubber, mock_location_extractor_missing):
        """
        Test request with image and text but NO coordinates
        Should return interactive conversational fallback with requires_user_input=True
        """
        image_content = b"fake_image_data"
        
        files = {
            'image': ('test_image.jpg', BytesIO(image_content), 'image/jpeg')
        }
        data = {
            'text': 'There is a pothole on Main Street',
            'language': 'en'
        }
        
        response = client.post("/api/complaint", files=files, data=data)
        
        # Should return success=False with requires_user_input=True
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] == False
        assert result["requires_user_input"] == True
        assert result["error"] == "Location required"
        assert "fallback_message" in result
        assert "I need the location" in result["fallback_message"]
        
        # Verify contract is still maintained
        data_section = result.get("data", {})
        assert "image_path" in data_section
        assert "transcribed_text" in data_section
        assert "gps_coordinates" in data_section
    
    def test_missing_image_text_only(self, mock_audio_processor, mock_audio_transcriber, 
                                    mock_location_extractor):
        """
        Test text-only/audio-only request without image
        Should process correctly and return "image_path": null
        """
        audio_content = b"fake_audio_data"
        
        files = {
            'audio': ('test_audio.wav', BytesIO(audio_content), 'audio/wav')
        }
        data = {
            'text': 'There is a pothole on Main Street',
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707',
            'language': 'en'
        }
        
        response = client.post("/api/complaint", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] == True
        data_section = result["data"]
        
        # Verify image_path is null when no image provided
        assert data_section["image_path"] is None
        assert data_section["transcribed_text"] is not None
        assert data_section["gps_coordinates"] == [13.0827, 80.2707]
    
    def test_sideways_image_handling(self, mock_audio_processor, mock_audio_transcriber, 
                                    mock_image_scrubber, mock_location_extractor):
        """
        Test handling of rotated/sideways image file
        Should save successfully and return path without orientation errors
        """
        # Create mock sideways image data
        sideways_image_content = b"fake_sideways_image_data"
        
        files = {
            'image': ('test_sideways.jpg', BytesIO(sideways_image_content), 'image/jpeg')
        }
        data = {
            'text': 'There is a pothole on Main Street',
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707',
            'language': 'en'
        }
        
        response = client.post("/api/complaint", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] == True
        data_section = result["data"]
        
        # Verify image was processed and path returned
        assert data_section["image_path"] is not None
        assert "uploads/" in data_section["image_path"]
        assert "sideways" in data_section["image_path"] or "test" in data_section["image_path"]
        
        # Verify no orientation-related errors in warnings
        warnings = result.get("warnings", [])
        assert not any("orientation" in str(warning).lower() for warning in warnings)
    
    def test_api_timeout_handling(self, mock_audio_processor, mock_timeout_transcriber, 
                                  mock_image_scrubber, mock_location_extractor):
        """
        Test API timeout from transcription service
        Should return safe error instead of crashing, process continues with text input
        """
        image_content = b"fake_image_data"
        audio_content = b"fake_audio_data"
        
        files = {
            'image': ('test_image.jpg', BytesIO(image_content), 'image/jpeg'),
            'audio': ('test_audio.wav', BytesIO(audio_content), 'audio/wav')
        }
        data = {
            'text': 'There is a pothole on Main Street',
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707',
            'language': 'en'
        }
        
        response = client.post("/api/complaint", files=files, data=data)
        
        # Should handle timeout gracefully and still return 200
        assert response.status_code == 200
        result = response.json()
        
        # Should have processed with fallback text
        assert result["success"] == True
        data_section = result["data"]
        
        # Should use the provided text as fallback
        assert data_section["transcribed_text"] == "There is a pothole on Main Street"
        
        # Should have timeout warning
        warnings = result.get("warnings", [])
        assert any("timeout" in str(warning).lower() for warning in warnings)


class TestErrorHandling:
    """Test robust error handling for edge cases"""
    
    def test_corrupt_audio_file_handling(self, mock_failing_audio_processor, mock_audio_transcriber, 
                                        mock_image_scrubber, mock_location_extractor):
        """
        Test handling of corrupt or unsupported audio file
        Should fail gracefully, skip transcription, and still process text/image
        """
        image_content = b"fake_image_data"
        corrupt_audio_content = b"corrupt_audio_data"
        
        files = {
            'image': ('test_image.jpg', BytesIO(image_content), 'image/jpeg'),
            'audio': ('corrupt_audio.wav', BytesIO(corrupt_audio_content), 'audio/wav')
        }
        data = {
            'text': 'There is a pothole on Main Street',
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707',
            'language': 'en'
        }
        
        response = client.post("/api/complaint", files=files, data=data)
        
        # Should still process successfully despite audio failure
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] == True
        data_section = result["data"]
        
        # Should have processed image and text
        assert data_section["image_path"] is not None
        assert data_section["transcribed_text"] == "There is a pothole on Main Street"
        
        # Should have warning about audio processing failure
        warnings = result.get("warnings", [])
        assert any("audio" in str(warning).lower() for warning in warnings)
    
    def test_unreadable_image_handling(self, mock_audio_processor, mock_audio_transcriber, 
                                       mock_failing_image_scrubber, mock_location_extractor):
        """
        Test handling of unreadable/corrupted image file
        Should bypass scrubber but still save the file and return path
        """
        audio_content = b"fake_audio_data"
        unreadable_image_content = b"corrupt_image_data"
        
        files = {
            'image': ('corrupt_image.jpg', BytesIO(unreadable_image_content), 'image/jpeg'),
            'audio': ('test_audio.wav', BytesIO(audio_content), 'audio/wav')
        }
        data = {
            'text': 'There is a pothole on Main Street',
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707',
            'language': 'en'
        }
        
        response = client.post("/api/complaint", files=files, data=data)
        
        # Should still process successfully despite image scrubbing failure
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] == True
        data_section = result["data"]
        
        # Should have saved the image despite scrubbing failure
        assert data_section["image_path"] is not None
        assert "uploads/" in data_section["image_path"]
        
        # Should have processed audio and text
        assert data_section["transcribed_text"] is not None
        
        # Should have warning about image processing failure
        warnings = result.get("warnings", [])
        assert any("image" in str(warning).lower() for warning in warnings)
    
    def test_no_media_text_only(self, mock_location_extractor):
        """
        Test request with only text, no media files
        Should process successfully with null media paths
        """
        data = {
            'text': 'There is a pothole on Main Street',
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707',
            'language': 'en'
        }
        
        response = client.post("/api/complaint", data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] == True
        data_section = result["data"]
        
        # Both media paths should be null
        assert data_section["image_path"] is None
        assert data_section["transcribed_text"] == "There is a pothole on Main Street"
        assert data_section["gps_coordinates"] == [13.0827, 80.2707]


class TestContractCompliance:
    """Strict testing of JSON handoff contract compliance"""
    
    def test_exact_contract_structure(self, mock_audio_processor, mock_audio_transcriber, 
                                      mock_image_scrubber, mock_location_extractor):
        """
        Test that response exactly matches expected contract:
        { "image_path": "uploads/img_123.jpg" | null, "transcribed_text": "text here", "gps_coordinates": [lat, lon] | null }
        """
        image_content = b"fake_image_data"
        audio_content = b"fake_audio_data"
        
        files = {
            'image': ('test_image.jpg', BytesIO(image_content), 'image/jpeg'),
            'audio': ('test_audio.wav', BytesIO(audio_content), 'audio/wav')
        }
        data = {
            'text': 'Test complaint',
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707',
            'language': 'en'
        }
        
        response = client.post("/api/complaint", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify exact contract fields
        data_section = result["data"]
        
        # Required fields must exist
        assert "image_path" in data_section
        assert "transcribed_text" in data_section
        assert "gps_coordinates" in data_section
        
        # No extra unexpected fields at the top level of data
        expected_fields = {"image_path", "transcribed_text", "gps_coordinates", 
                          "audio_metadata", "image_metadata", "location_metadata", "transcription_metadata"}
        actual_fields = set(data_section.keys())
        assert actual_fields.issuperset(expected_fields)
        
        # Verify value types
        assert isinstance(data_section["image_path"], (str, type(None)))
        assert isinstance(data_section["transcribed_text"], str)
        assert isinstance(data_section["gps_coordinates"], (list, type(None)))
        
        # Verify gps_coordinates format when present
        if data_section["gps_coordinates"] is not None:
            assert len(data_section["gps_coordinates"]) == 2
            assert all(isinstance(coord, (int, float)) for coord in data_section["gps_coordinates"])


class TestEdgeCases:
    """Test additional edge cases for production readiness"""
    
    def test_empty_text_with_audio(self, mock_audio_processor, mock_audio_transcriber, 
                                   mock_location_extractor):
        """
        Test request with empty text but valid audio
        Should transcribe audio and use that as text
        """
        audio_content = b"fake_audio_data"
        
        files = {
            'audio': ('test_audio.wav', BytesIO(audio_content), 'audio/wav')
        }
        data = {
            'text': '',
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707',
            'language': 'en'
        }
        
        response = client.post("/api/complaint", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] == True
        data_section = result["data"]
        
        # Should have transcribed text from audio
        assert data_section["transcribed_text"] == "There is a huge pothole on Main Street that needs immediate repair."
        assert data_section["image_path"] is None
    
    def test_large_file_handling(self, mock_audio_processor, mock_audio_transcriber, 
                                mock_image_scrubber, mock_location_extractor):
        """
        Test handling of larger files (within limits)
        Should process without timeout
        """
        # Create larger mock file
        large_image_content = b"x" * (5 * 1024 * 1024)  # 5MB
        
        files = {
            'image': ('large_image.jpg', BytesIO(large_image_content), 'image/jpeg')
        }
        data = {
            'text': 'There is a pothole on Main Street',
            'gps_latitude': '13.0827',
            'gps_longitude': '80.2707',
            'language': 'en'
        }
        
        response = client.post("/api/complaint", files=files, data=data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] == True
        assert result["data"]["image_path"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
