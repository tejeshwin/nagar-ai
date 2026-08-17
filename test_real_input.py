"""
Interactive Test Script for Civic Complaint Intelligence Engine
Allows real user input testing with text and audio files
"""
import os
import sys
from pathlib import Path
import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            result = response.json()
            print("✅ Server is running!")
            print(f"Status: {result['status']}")
            print(f"Transcription Provider: {result['components']['transcription_provider']}")
            return True
        else:
            print("❌ Server is not responding correctly")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Make sure the server is running: python main.py")
        return False

def submit_text_complaint():
    """Submit a text-based complaint"""
    print("\n=== Submit Text Complaint ===")
    text = input("Enter your complaint text: ")
    
    if not text.strip():
        print("❌ Text cannot be empty")
        return None
    
    data = {
        'text': text
    }
    
    # Ask for GPS coordinates
    use_gps = input("Do you have GPS coordinates? (y/n): ").lower()
    if use_gps == 'y':
        try:
            lat = float(input("Enter latitude: "))
            lon = float(input("Enter longitude: "))
            data['gps_latitude'] = lat
            data['gps_longitude'] = lon
        except ValueError:
            print("⚠️ Invalid GPS coordinates, submitting without location")
    
    try:
        response = requests.post(f"{BASE_URL}/api/complaint", data=data)
        result = response.json()
        
        print("\n=== Response ===")
        print(json.dumps(result, indent=2))
        
        if result.get('requires_user_input'):
            handle_location_fallback(result['complaint_id'])
        
        return result
    except Exception as e:
        print(f"❌ Error submitting complaint: {e}")
        return None

def submit_audio_complaint():
    """Submit an audio-based complaint"""
    print("\n=== Submit Audio Complaint ===")
    
    audio_path = input("Enter path to audio file (mp3, wav, m4a, ogg): ")
    
    if not os.path.exists(audio_path):
        print(f"❌ File not found: {audio_path}")
        return None
    
    # Ask for language
    language = input("Enter language code (e.g., 'ta' for Tamil, 'hi' for Hindi, 'en' for English): ")
    
    # Ask for GPS coordinates
    use_gps = input("Do you have GPS coordinates? (y/n): ").lower()
    data = {}
    if use_gps == 'y':
        try:
            lat = float(input("Enter latitude: "))
            lon = float(input("Enter longitude: "))
            data['gps_latitude'] = lat
            data['gps_longitude'] = lon
        except ValueError:
            print("⚠️ Invalid GPS coordinates, submitting without location")
    
    if language:
        data['language'] = language
    
    try:
        with open(audio_path, 'rb') as audio_file:
            files = {'audio': audio_file}
            response = requests.post(f"{BASE_URL}/api/complaint", files=files, data=data)
        
        result = response.json()
        
        print("\n=== Response ===")
        print(json.dumps(result, indent=2))
        
        if result.get('requires_user_input'):
            handle_location_fallback(result['complaint_id'])
        
        return result
    except Exception as e:
        print(f"❌ Error submitting audio complaint: {e}")
        return None

def submit_image_complaint():
    """Submit an image-based complaint"""
    print("\n=== Submit Image Complaint ===")
    
    image_path = input("Enter path to image file (jpg, jpeg, png): ")
    
    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        return None
    
    text = input("Enter description (optional, press Enter to skip): ")
    
    # Ask for GPS coordinates
    use_gps = input("Do you have GPS coordinates? (y/n): ").lower()
    data = {}
    if use_gps == 'y':
        try:
            lat = float(input("Enter latitude: "))
            lon = float(input("Enter longitude: "))
            data['gps_latitude'] = lat
            data['gps_longitude'] = lon
        except ValueError:
            print("⚠️ Invalid GPS coordinates, submitting without location")
    
    if text:
        data['text'] = text
    
    try:
        with open(image_path, 'rb') as image_file:
            files = {'image': image_file}
            response = requests.post(f"{BASE_URL}/api/complaint", files=files, data=data)
        
        result = response.json()
        
        print("\n=== Response ===")
        print(json.dumps(result, indent=2))
        
        if result.get('requires_user_input'):
            handle_location_fallback(result['complaint_id'])
        
        return result
    except Exception as e:
        print(f"❌ Error submitting image complaint: {e}")
        return None

def submit_full_complaint():
    """Submit a complaint with text, audio, and image"""
    print("\n=== Submit Full Complaint (Text + Audio + Image) ===")
    
    text = input("Enter your complaint text: ")
    
    audio_path = input("Enter path to audio file (optional, press Enter to skip): ")
    image_path = input("Enter path to image file (optional, press Enter to skip): ")
    
    language = input("Enter language code (e.g., 'ta' for Tamil, 'hi' for Hindi): ")
    
    # Ask for GPS coordinates
    use_gps = input("Do you have GPS coordinates? (y/n): ").lower()
    data = {}
    if use_gps == 'y':
        try:
            lat = float(input("Enter latitude: "))
            lon = float(input("Enter longitude: "))
            data['gps_latitude'] = lat
            data['gps_longitude'] = lon
        except ValueError:
            print("⚠️ Invalid GPS coordinates, submitting without location")
    
    if text:
        data['text'] = text
    if language:
        data['language'] = language
    
    files = {}
    if audio_path and os.path.exists(audio_path):
        files['audio'] = open(audio_path, 'rb')
    if image_path and os.path.exists(image_path):
        files['image'] = open(image_path, 'rb')
    
    if not files and not text:
        print("❌ No data provided")
        return None
    
    try:
        response = requests.post(f"{BASE_URL}/api/complaint", files=files, data=data)
        
        # Close files
        for file in files.values():
            file.close()
        
        result = response.json()
        
        print("\n=== Response ===")
        print(json.dumps(result, indent=2))
        
        if result.get('requires_user_input'):
            handle_location_fallback(result['complaint_id'])
        
        return result
    except Exception as e:
        print(f"❌ Error submitting full complaint: {e}")
        return None

def handle_location_fallback(complaint_id):
    """Handle location fallback scenario"""
    print(f"\n⚠️ Location information required for complaint {complaint_id}")
    print("The system needs location to process your complaint.")
    
    location_input = input("Enter GPS coordinates (lat,lon) or address: ")
    
    if not location_input.strip():
        print("❌ Location input cannot be empty")
        return
    
    try:
        location_data = {
            "complaint_id": complaint_id,
            "location_input": location_input
        }
        
        response = requests.post(f"{BASE_URL}/api/complaint/{complaint_id}/location", json=location_data)
        result = response.json()
        
        print("\n=== Location Update Response ===")
        print(json.dumps(result, indent=2))
        
        if result.get('success'):
            print("✅ Location updated successfully!")
        else:
            print("⚠️ Location update failed, please try again")
            
    except Exception as e:
        print(f"❌ Error updating location: {e}")

def get_complaint_details():
    """Get details of a specific complaint"""
    print("\n=== Get Complaint Details ===")
    complaint_id = input("Enter complaint ID: ")
    
    try:
        response = requests.get(f"{BASE_URL}/api/complaint/{complaint_id}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n=== Complaint Details ===")
            print(json.dumps(result, indent=2))
            return result
        else:
            print(f"❌ Complaint not found (status: {response.status_code})")
            return None
    except Exception as e:
        print(f"❌ Error getting complaint: {e}")
        return None

def list_all_complaints():
    """List all complaints"""
    print("\n=== All Complaints ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/complaints")
        result = response.json()
        
        print(f"Total complaints: {result['total_complaints']}")
        print("\nComplaints:")
        for complaint in result['complaints']:
            print(f"  ID: {complaint['complaint_id']}")
            print(f"  Timestamp: {complaint['timestamp']}")
            print(f"  Has Location: {complaint['has_location']}")
            print(f"  Has Image: {complaint['has_image']}")
            print(f"  Has Audio: {complaint['has_audio']}")
            print()
            
    except Exception as e:
        print(f"❌ Error listing complaints: {e}")

def main_menu():
    """Main menu for interactive testing"""
    print("\n" + "="*50)
    print("Civic Complaint Intelligence Engine - Interactive Test")
    print("="*50)
    
    while True:
        print("\n=== Main Menu ===")
        print("1. Test Server Health")
        print("2. Submit Text Complaint")
        print("3. Submit Audio Complaint")
        print("4. Submit Image Complaint")
        print("5. Submit Full Complaint (Text + Audio + Image)")
        print("6. Get Complaint Details")
        print("7. List All Complaints")
        print("8. Exit")
        
        choice = input("\nEnter your choice (1-8): ")
        
        if choice == '1':
            test_health()
        elif choice == '2':
            submit_text_complaint()
        elif choice == '3':
            submit_audio_complaint()
        elif choice == '4':
            submit_image_complaint()
        elif choice == '5':
            submit_full_complaint()
        elif choice == '6':
            get_complaint_details()
        elif choice == '7':
            list_all_complaints()
        elif choice == '8':
            print("Exiting...")
            break
        else:
            print("❌ Invalid choice, please try again")

if __name__ == "__main__":
    print("🚀 Starting Interactive Test Client...")
    print("Make sure the server is running: python main.py")
    print()
    
    # First check if server is running
    if test_health():
        main_menu()
    else:
        print("\n❌ Please start the server first:")
        print("   cd C:\\Users\\Tejeshwin.D\\civic_complaint_engine")
        print("   python main.py")
