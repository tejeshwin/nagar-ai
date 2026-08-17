# 🚀 Quick Start Guide

Get the Civic Complaint Intelligence Engine backend running in 5 minutes!

## Step 1: Install Dependencies

```bash
# Navigate to project directory
cd civic_complaint_engine

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Install FFmpeg (Required for audio processing)

**Windows:**
1. Download from: https://ffmpeg.org/download.html
2. Extract and add to system PATH
3. Verify: `ffmpeg -version`

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg
```

## Step 3: Configure API Keys

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# Get your key from: https://platform.openai.com/api-keys
```

Edit `.env`:
```env
OPENAI_API_KEY=sk-your-actual-key-here
```

## Step 4: Start the Server

```bash
python main.py
```

Server will start at: `http://localhost:8000`

## Step 5: Test the API

Open a new terminal and run:

```bash
python test_api.py
```

Or test manually:

```bash
# Health check
curl http://localhost:8000/health

# Submit a text complaint
curl -X POST "http://localhost:8000/api/complaint" \
  -F "text=There is a pothole on Main Street"
```

## 🎯 What You've Built

Your backend now includes:

✅ **Edge-Processed Audio Compression** - Reduces costs, handles noise
✅ **Privacy-by-Design Image Scrubber** - Blurs faces/license plates  
✅ **Interactive Location Fallback** - Ensures location capture
✅ **Multi-language Support** - Tamil, Hindi, English
✅ **Robust Error Handling** - Graceful degradation
✅ **Production-Ready API** - FastAPI with proper documentation

## 📡 Key Endpoints

- `POST /api/complaint` - Submit complaints (text, audio, image, GPS)
- `POST /api/complaint/{id}/location` - Update missing location
- `GET /api/complaint/{id}` - Retrieve complaint details
- `GET /health` - System health check

## 🔗 Integration with Your Dashboard

Your dashboard can now:

1. **Submit complaints** via POST to `/api/complaint`
2. **Handle location fallback** when `requires_user_input=true`
3. **Receive standardized output** with image path, transcribed text, and GPS coordinates

## 🏆 Ready for the Hackathon!

The backend is ready to handle:
- Background noise in audio ✅
- Mixed languages (Tamil/Hindi/English) ✅  
- Sideways photos (preserved as-is) ✅
- Missing location data (interactive fallback) ✅

Good luck with your hackathon! 🎉
