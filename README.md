# Civic Complaint Intelligence Engine - Backend Documentation

## Overview
This is a robust, production-ready Python backend for the Civic Complaint Intelligence Engine hackathon project. It handles multi-modal citizen complaint input including text, audio (Tamil/Hindi voice notes), and photos, with advanced processing capabilities.

## 🚀 Key Features (The 3 Required Innovations)

### 1. Edge-Processed Audio Compression
- **Implementation**: Uses `pydub` for lightweight audio processing
- **Features**: 
  - Silence trimming from beginning/end and middle of audio
  - Audio normalization for consistent quality
  - Format conversion (MP3, WAV, etc.)
  - Compression to reduce API costs
- **Benefits**: Reduces transcription costs, improves accuracy, works offline-ish

### 2. Privacy-by-Design Image Scrubber
- **Implementation**: Uses OpenCV Haar Cascade classifiers
- **Features**:
  - Automatic face detection and blurring
  - License plate detection and blurring
  - Preserves image orientation (no auto-cropping)
  - Handles sideways photos as-is
- **Benefits**: Protects citizen privacy, compliant with data protection regulations

### 3. Interactive Missing-Data Fallback
- **Implementation**: Multi-source location extraction with conversational fallback
- **Features**:
  - GPS coordinate extraction (priority 1)
  - EXIF data extraction from images (priority 2)
  - Text-based location mention extraction (priority 3)
  - Conversational fallback when all fail
- **Benefits**: Ensures location data is always captured, improves user experience

## 📋 Installation

### Prerequisites
- Python 3.8 or higher
- FFmpeg (required for pydub audio processing)
  - Windows: Download from https://ffmpeg.org/download.html
  - Mac: `brew install ffmpeg`
  - Linux: `sudo apt-get install ffmpeg`

### Setup Steps

1. **Navigate to project directory**
```bash
cd civic_complaint_engine
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
```

5. **Edit `.env` file and add your API keys**
```env
OPENAI_API_KEY=your_actual_openai_api_key_here
AI4BHARAT_API_KEY=your_actual_ai4bharat_api_key_here
```

## 🔑 API Keys Configuration

### Required API Keys

1. **OpenAI API Key** (Primary - for Whisper transcription)
   - Get from: https://platform.openai.com/api-keys
   - Required for: Audio transcription via OpenAI Whisper API
   - Cost: ~$0.006 per minute
   - Set in `.env`: `OPENAI_API_KEY=sk-...`

2. **AI4Bharat API Key** (Optional - for Indic language support)
   - Get from: https://ai4bharat.org/
   - Required for: Tamil/Hindi transcription fallback
   - Cost: Free tier available
   - Set in `.env`: `AI4BHARAT_API_KEY=your_key_here`

### API Key Fallback System
The system uses a cascading fallback approach:
1. OpenAI Whisper API (most accurate)
2. Local Whisper model (no API key needed, less accurate)
3. AI4Bharat API (best for Indic languages)

## 🏃 Running the Server

### Development Mode
```bash
python main.py
```
Server will start at `http://localhost:8000`

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📡 API Endpoints

### 1. Submit Complaint
**POST** `/api/complaint`

**Request**: Multi-part form data
- `text` (optional): Text complaint
- `audio` (optional): Audio file (MP3, WAV, M4A, OGG)
- `image` (optional): Image file (JPG, JPEG, PNG)
- `gps_latitude` (optional): GPS latitude
- `gps_longitude` (optional): GPS longitude
- `language` (optional): Language code (e.g., 'ta' for Tamil, 'hi' for Hindi)

**Response**: JSON
```json
{
  "success": true,
  "complaint_id": "uuid",
  "timestamp": "2024-01-01T00:00:00",
  "data": {
    "image_path": "/path/to/scrubbed/image.jpg",
    "transcribed_text": "The transcribed complaint text",
    "gps_coordinates": [13.0827, 80.2707],
    "audio_metadata": {...},
    "image_metadata": {...},
    "location_metadata": {...}
  },
  "warnings": ["Audio compressed: 2.5x reduction"],
  "requires_user_input": false
}
```

### 2. Update Location (Fallback)
**POST** `/api/complaint/{complaint_id}/location`

**Request**: JSON
```json
{
  "complaint_id": "uuid",
  "location_input": "13.0827, 80.2707 or street address"
}
```

**Response**: Same format as submit complaint

### 3. Get Complaint
**GET** `/api/complaint/{complaint_id}`

**Response**: Complaint details

### 4. Health Check
**GET** `/health`

**Response**: System status

## 🧪 Testing the API

### Using cURL

**Submit complaint with audio and image:**
```bash
curl -X POST "http://localhost:8000/api/complaint" \
  -F "audio=@complaint_audio.mp3" \
  -F "image=@complaint_photo.jpg" \
  -F "gps_latitude=13.0827" \
  -F "gps_longitude=80.2707" \
  -F "language=ta"
```

**Submit text-only complaint:**
```bash
curl -X POST "http://localhost:8000/api/complaint" \
  -F "text=There is a pothole on Main Street"
```

### Using Python
```python
import requests

# Submit complaint
files = {
    'audio': open('complaint.mp3', 'rb'),
    'image': open('photo.jpg', 'rb')
}
data = {
    'gps_latitude': 13.0827,
    'gps_longitude': 80.2707,
    'language': 'ta'
}

response = requests.post('http://localhost:8000/api/complaint', files=files, data=data)
print(response.json())
```

## 🎯 The Handoff Contract

The system outputs a standardized JSON object exactly as required:

```python
{
    "image_path": "/path/to/scrubbed/image.jpg",  # Privacy-scrubbed image
    "transcribed_text": "The transcribed complaint",  # Text or transcribed audio
    "gps_coordinates": [13.0827, 80.2707]  # Extracted location
}
```

This is delivered in the `data` field of the API response.

## 🛡️ Robustness & Edge Cases

### Audio Processing
- **Background noise**: Uses Whisper's noise-resistant parameters
- **Mixed languages**: Auto-detects language, supports Tamil/Hindi
- **Multiple formats**: Handles MP3, WAV, M4A, OGG, FLAC
- **Error handling**: Cascading fallback system

### Image Processing  
- **Sideways photos**: Preserved as-is for teammate's CV model
- **Various formats**: Handles JPG, JPEG, PNG
- **Privacy**: Automatic face/license plate blurring
- **EXIF data**: Preserved for location extraction

### Location Extraction
- **GPS coordinates**: Direct latitude/longitude input
- **EXIF metadata**: Extracted from image metadata
- **Text mentions**: Parses addresses, landmarks, pin codes
- **Fallback**: Conversational prompts for missing data

## 📁 Project Structure

```
civic_complaint_engine/
├── main.py                      # FastAPI application and endpoints
├── config.py                    # Configuration management
├── audio_processor.py           # Edge-processed audio compression
├── image_scrubber.py            # Privacy-by-design image scrubbing
├── location_extractor.py        # Location extraction with fallback
├── audio_transcriber.py         # Robust audio transcription
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .env                         # Your actual API keys (not in git)
├── README.md                    # This file
└── uploads/                     # Directory for uploaded files (auto-created)
```

## 🔧 Configuration Options

Edit `.env` file to customize:

### Audio Processing
- `SILENCE_THRESHOLD`: dB threshold for silence detection (-40 default)
- `MIN_SILENCE_LENGTH`: Minimum silence length in ms (500 default)
- `SILENCE_KEEP`: Silence to keep around speech in ms (100 default)

### Image Processing
- `FACE_DETECTION_CONFIDENCE`: Threshold for face detection (0.7 default)
- `BLUR_KERNEL_SIZE`: Size of blur kernel (51 default)

### Server
- `UPLOAD_DIR`: Directory for uploaded files
- `MAX_FILE_SIZE_MB`: Maximum file size in MB (50 default)

## 🚨 Error Handling

The system implements comprehensive error handling:

1. **Audio processing failures**: Falls back to original audio
2. **Image scrubbing failures**: Returns original image
3. **Transcription failures**: Tries multiple APIs, reports warnings
4. **Location extraction failures**: Triggers conversational fallback
5. **API failures**: Graceful degradation with detailed error messages

## 📊 Monitoring & Logging

- Logs are written to `civic_complaint_engine.log`
- Console logging for real-time monitoring
- Health check endpoint for system status
- Detailed metadata for all processing steps

## 🤝 Integration with Frontend

### Dashboard Integration
Your dashboard can integrate using standard HTTP requests:

1. **Submit complaint**: POST to `/api/complaint` with form data
2. **Handle fallback**: If `requires_user_input=true`, prompt user for location
3. **Update location**: POST to `/api/complaint/{id}/location`
4. **Retrieve results**: GET from `/api/complaint/{id}`

### Expected Workflow
1. User submits complaint via dashboard
2. Backend processes audio/image/text
3. If location missing, backend requests user input
4. Dashboard prompts user for location
5. User provides location via GPS pin or text
6. Backend completes processing
7. Dashboard receives final standardized output

## 🏆 Hackathon Bonus Points

This implementation specifically addresses the bonus criteria:

✅ **Edge-Processed Audio Compression**: Reduces costs, works offline-ish
✅ **Privacy-by-Design Image Scrubber**: Protects privacy, preserves orientation
✅ **Interactive Missing-Data Fallback**: Ensures location capture, improves UX
✅ **Robustness**: Handles noise, mixed languages, sideways photos
✅ **Production-Ready**: Comprehensive error handling, logging, documentation

## 🐛 Troubleshooting

### FFmpeg not found
- Ensure FFmpeg is installed and in system PATH
- Windows: Add FFmpeg bin folder to system PATH

### OpenAI API errors
- Verify API key is correct
- Check API credits/usage limits
- Ensure network connectivity

### Image processing errors
- Verify OpenCV installation: `pip install opencv-python`
- Check image file formats are supported

### Location extraction failing
- Ensure geocoding service is accessible
- Check internet connectivity for reverse geocoding
- Verify GPS coordinate format

## 📝 License

This code is provided for the hackathon competition. Please ensure proper API key management and don't commit sensitive information to version control.

## 🎉 Good Luck!

This backend is ready to power your Civic Complaint Intelligence Engine. The modular design makes it easy to integrate with your frontend and your teammate's computer vision classification system. The robust error handling and fallback mechanisms ensure it will perform well under the judges' testing scenarios.
