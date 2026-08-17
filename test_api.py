"""
Test script for Civic Complaint Intelligence Engine API
Demonstrates how to interact with the backend endpoints
"""
import requests
import json
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_text_complaint():
    """Test submitting a text-only complaint"""
    print("Testing text-only complaint...")
    
    data = {
        "text": "There is a huge pothole on Main Street near the market that needs immediate repair."
    }
    
    response = requests.post(f"{BASE_URL}/api/complaint", data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    return response.json()

def test_complaint_with_location():
    """Test complaint with GPS coordinates"""
    print("Testing complaint with GPS coordinates...")
    
    data = {
        "text": "Street lights are not working on Anna Nagar 3rd Street",
        "gps_latitude": 13.0827,
        "gps_longitude": 80.2707
    }
    
    response = requests.post(f"{BASE_URL}/api/complaint", data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    return response.json()

def test_complaint_with_audio(image_path=None):
    """Test complaint with audio file"""
    print("Testing complaint with audio...")
    
    # Note: You need to provide an actual audio file
    audio_path = "sample_audio.mp3"  # Replace with actual file
    
    if not Path(audio_path).exists():
        print(f"Audio file not found: {audio_path}")
        print("Please provide a valid audio file to test this endpoint")
        print()
        return None
    
    files = {'audio': open(audio_path, 'rb')}
    data = {
        "language": "ta",  # Tamil
        "gps_latitude": 13.0827,
        "gps_longitude": 80.2707
    }
    
    response = requests.post(f"{BASE_URL}/api/complaint", files=files, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    return response.json()

def test_complaint_with_image():
    """Test complaint with image file"""
    print("Testing complaint with image...")
    
    # Note: You need to provide an actual image file
    image_path = "sample_image.jpg"  # Replace with actual file
    
    if not Path(image_path).exists():
        print(f"Image file not found: {image_path}")
        print("Please provide a valid image file to test this endpoint")
        print()
        return None
    
    files = {'image': open(image_path, 'rb')}
    data = {
        "text": "Garbage pile near the bus stand needs cleaning",
        "gps_latitude": 13.0827,
        "gps_longitude": 80.2707
    }
    
    response = requests.post(f"{BASE_URL}/api/complaint", files=files, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    return response.json()

def test_location_fallback():
    """Test the location fallback mechanism"""
    print("Testing location fallback (no location provided)...")
    
    data = {
        "text": "There is a broken water pipe in my area"
    }
    
    response = requests.post(f"{BASE_URL}/api/complaint", data=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    # If location is required, test the fallback endpoint
    if result.get('requires_user_input'):
        print("Location required - testing fallback endpoint...")
        
        complaint_id = result.get('complaint_id')
        location_data = {
            "complaint_id": complaint_id,
            "location_input": "13.0827, 80.2707"  # Could also be "Main Street, Chennai"
        }
        
        fallback_response = requests.post(
            f"{BASE_URL}/api/complaint/{complaint_id}/location",
            json=location_data
        )
        print(f"Fallback Status: {fallback_response.status_code}")
        print(f"Fallback Response: {json.dumps(fallback_response.json(), indent=2)}")
    
    print()

def test_get_complaint(complaint_id):
    """Test retrieving a specific complaint"""
    print(f"Testing get complaint {complaint_id}...")
    
    response = requests.get(f"{BASE_URL}/api/complaint/{complaint_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_list_complaints():
    """Test listing all complaints"""
    print("Testing list all complaints...")
    
    response = requests.get(f"{BASE_URL}/api/complaints")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def main():
    """Run all tests"""
    print("=" * 50)
    print("Civic Complaint Intelligence Engine - API Tests")
    print("=" * 50)
    print()
    
    try:
        # Test health check
        test_health_check()
        
        # Test text complaint
        text_result = test_text_complaint()
        
        # Test complaint with location
        location_result = test_complaint_with_location()
        
        # Test location fallback
        test_location_fallback()
        
        # Test complaint with image (if file exists)
        test_complaint_with_image()
        
        # Test complaint with audio (if file exists)
        test_complaint_with_audio()
        
        # List all complaints
        test_list_complaints()
        
        # Get specific complaint if available
        if text_result:
            test_get_complaint(text_result.get('complaint_id'))
        
        print("=" * 50)
        print("Tests completed!")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server.")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    main()
