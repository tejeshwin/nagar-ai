# 🔌 Dashboard Integration Guide

This guide explains how to integrate your frontend dashboard with the Civic Complaint Intelligence Engine backend.

## 📋 API Overview

The backend provides a RESTful API with the following endpoints:

### Base URL
```
http://localhost:8000
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Check system health |
| POST | `/api/complaint` | Submit new complaint |
| POST | `/api/complaint/{id}/location` | Update missing location |
| GET | `/api/complaint/{id}` | Get complaint details |
| GET | `/api/complaints` | List all complaints |

## 🎯 Integration Workflow

### 1. Submit Complaint

**Endpoint:** `POST /api/complaint`

**Request Format:** Multi-part form data

```javascript
// JavaScript/Fetch API example
const formData = new FormData();

// Add text complaint (optional)
formData.append('text', 'There is a pothole on Main Street');

// Add audio file (optional)
formData.append('audio', audioFile);

// Add image file (optional)  
formData.append('image', imageFile);

// Add GPS coordinates (optional)
formData.append('gps_latitude', '13.0827');
formData.append('gps_longitude', '80.2707');

// Add language hint (optional) - 'ta' for Tamil, 'hi' for Hindi
formData.append('language', 'ta');

// Submit
const response = await fetch('http://localhost:8000/api/complaint', {
    method: 'POST',
    body: formData
});

const result = await response.json();
```

**Response Format:**

```json
{
  "success": true,
  "complaint_id": "uuid-string",
  "timestamp": "2024-01-01T00:00:00",
  "data": {
    "image_path": "/path/to/scrubbed/image.jpg",
    "transcribed_text": "The transcribed complaint text",
    "gps_coordinates": [13.0827, 80.2707],
    "audio_metadata": {
      "compression_ratio": 2.5,
      "original_duration": 30.5,
      "processed_duration": 25.2
    },
    "image_metadata": {
      "faces_detected": 2,
      "license_plates_detected": 0,
      "scrubbed_regions": [...]
    },
    "location_metadata": {
      "source": "gps",
      "confidence": 1.0,
      "address": "Chennai, Tamil Nadu, India"
    },
    "transcription_metadata": {
      "language": "ta",
      "confidence": 0.9,
      "method": "openai_whisper"
    }
  },
  "warnings": ["Audio compressed: 2.5x reduction"],
  "requires_user_input": false,
  "fallback_message": null
}
```

### 2. Handle Location Fallback

If `requires_user_input` is `true`, you need to prompt the user for location:

```javascript
if (result.requires_user_input) {
    // Show user the fallback message
    alert(result.fallback_message);
    
    // Prompt user for location (GPS pin or text)
    const userLocation = prompt("Please enter GPS coordinates or address:");
    
    // Submit location update
    const locationResponse = await fetch(
        `http://localhost:8000/api/complaint/${result.complaint_id}/location`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                complaint_id: result.complaint_id,
                location_input: userLocation
            })
        }
    );
    
    const locationResult = await locationResponse.json();
    
    if (locationResult.success) {
        console.log('Location updated successfully');
        console.log('Final data:', locationResult.data);
    }
}
```

### 3. Retrieve Complaint Details

```javascript
const response = await fetch(`http://localhost:8000/api/complaint/${complaintId}`);
const complaint = await response.json();
```

## 🎨 Frontend Implementation Examples

### React Example

```jsx
import React, { useState } from 'react';

function ComplaintForm() {
    const [text, setText] = useState('');
    const [audio, setAudio] = useState(null);
    const [image, setImage] = useState(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);

        const formData = new FormData();
        formData.append('text', text);
        if (audio) formData.append('audio', audio);
        if (image) formData.append('image', image);

        try {
            const response = await fetch('http://localhost:8000/api/complaint', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            setResult(data);

            // Handle location fallback
            if (data.requires_user_input) {
                const userLocation = prompt(data.fallback_message);
                if (userLocation) {
                    await updateLocation(data.complaint_id, userLocation);
                }
            }
        } catch (error) {
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
    };

    const updateLocation = async (complaintId, locationInput) => {
        const response = await fetch(
            `http://localhost:8000/api/complaint/${complaintId}/location`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ complaint_id: complaintId, location_input: locationInput })
            }
        );
        const data = await response.json();
        setResult(data);
    };

    return (
        <form onSubmit={handleSubmit}>
            <textarea 
                value={text} 
                onChange={(e) => setText(e.target.value)}
                placeholder="Describe your complaint..."
            />
            <input 
                type="file" 
                accept="audio/*"
                onChange={(e) => setAudio(e.target.files[0])}
            />
            <input 
                type="file" 
                accept="image/*"
                onChange={(e) => setImage(e.target.files[0])}
            />
            <button type="submit" disabled={loading}>
                {loading ? 'Processing...' : 'Submit Complaint'}
            </button>
            
            {result && (
                <div>
                    <h3>Result:</h3>
                    <pre>{JSON.stringify(result, null, 2)}</pre>
                </div>
            )}
        </form>
    );
}
```

### HTML/JavaScript Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>Civic Complaint Form</title>
</head>
<body>
    <h1>Submit Civic Complaint</h1>
    
    <form id="complaintForm">
        <textarea id="text" placeholder="Describe your complaint..."></textarea><br><br>
        
        <label>Audio (optional):</label>
        <input type="file" id="audio" accept="audio/*"><br><br>
        
        <label>Image (optional):</label>
        <input type="file" id="image" accept="image/*"><br><br>
        
        <label>GPS Latitude (optional):</label>
        <input type="text" id="latitude" placeholder="13.0827"><br><br>
        
        <label>GPS Longitude (optional):</label>
        <input type="text" id="longitude" placeholder="80.2707"><br><br>
        
        <button type="submit">Submit Complaint</button>
    </form>
    
    <div id="result"></div>
    
    <script>
        document.getElementById('complaintForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData();
            formData.append('text', document.getElementById('text').value);
            
            const audioFile = document.getElementById('audio').files[0];
            if (audioFile) formData.append('audio', audioFile);
            
            const imageFile = document.getElementById('image').files[0];
            if (imageFile) formData.append('image', imageFile);
            
            const latitude = document.getElementById('latitude').value;
            const longitude = document.getElementById('longitude').value;
            if (latitude) formData.append('gps_latitude', latitude);
            if (longitude) formData.append('gps_longitude', longitude);
            
            try {
                const response = await fetch('http://localhost:8000/api/complaint', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                
                document.getElementById('result').innerHTML = 
                    '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
                
                // Handle location fallback
                if (result.requires_user_input) {
                    const userLocation = prompt(result.fallback_message);
                    if (userLocation) {
                        await updateLocation(result.complaint_id, userLocation);
                    }
                }
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('result').innerHTML = 
                    '<p style="color: red;">Error submitting complaint</p>';
            }
        });
        
        async function updateLocation(complaintId, locationInput) {
            const response = await fetch(
                `http://localhost:8000/api/complaint/${complaintId}/location`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        complaint_id: complaintId,
                        location_input: locationInput
                    })
                }
            );
            const result = await response.json();
            document.getElementById('result').innerHTML = 
                '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
        }
    </script>
</body>
</html>
```

## 🔄 Complete Data Flow

```
1. User submits complaint via dashboard
   ↓
2. Dashboard sends POST to /api/complaint
   ↓
3. Backend processes:
   - Audio compression & transcription
   - Image privacy scrubbing
   - Location extraction
   ↓
4a. If location found: Return complete data
   ↓
4b. If location missing: Return requires_user_input=true
   ↓
5. Dashboard prompts user for location
   ↓
6. User provides GPS pin or address
   ↓
7. Dashboard sends POST to /api/complaint/{id}/location
   ↓
8. Backend returns complete processed data
   ↓
9. Dashboard receives standardized output:
   {
     "image_path": "/path/to/image.jpg",
     "transcribed_text": "complaint text",
     "gps_coordinates": [lat, lon]
   }
```

## 🎯 The Handoff Contract

Your dashboard will receive exactly this format in the `data` field:

```json
{
  "image_path": "/path/to/scrubbed/image.jpg",
  "transcribed_text": "The complaint text (or transcribed audio)",
  "gps_coordinates": [13.0827, 80.2707]
}
```

This is ready to be passed to your teammate's computer vision classification system.

## 🚨 Error Handling

Implement proper error handling in your dashboard:

```javascript
try {
    const response = await fetch('http://localhost:8000/api/complaint', {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (!result.success) {
        console.error('Server error:', result.error);
        // Handle error
    }
    
    // Process successful result
} catch (error) {
    console.error('Network error:', error);
    // Show user-friendly error message
}
```

## 🔒 Security Considerations

1. **API Keys**: Never expose API keys in frontend code
2. **File Uploads**: Validate file types and sizes on frontend
3. **HTTPS**: Use HTTPS in production
4. **CORS**: Configure CORS appropriately for your domain
5. **Rate Limiting**: Implement rate limiting on your dashboard

## 📱 Mobile Integration

For mobile apps (React Native, Flutter, etc.):

- Use the same API endpoints
- Handle file uploads with appropriate mobile file pickers
- Implement GPS location capture using device APIs
- Use the same fallback flow for missing location

## 🎉 Integration Complete!

Your dashboard is now ready to submit complaints to the Civic Complaint Intelligence Engine backend. The system will handle all the complex processing and return clean, standardized data for your teammate's computer vision classification.
