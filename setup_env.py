"""
Script to create .env file with Llama API key
Run this script to automatically create your .env file
"""
import os
from pathlib import Path

def create_env_file():
    """Create .env file with Llama API configuration"""
    
    # Your Sarvam AI API key
    sarvam_api_key = "sk_w41obl45_LQ7jjtsxbUB7SRrjFdllwfS0"
    
    env_content = f"""# API Keys Configuration
# Using Sarvam AI API for audio transcription

# Sarvam AI API Key for transcription
SARVAM_API_KEY={sarvam_api_key}

# Alternative: OpenAI API Key (optional, if you want to use OpenAI as fallback)
# OPENAI_API_KEY=your_openai_api_key_here

# Alternative: AI4Bharat API Key (optional, for Indic language support)
# AI4BHARAT_API_KEY=your_ai4bharat_api_key_here

# Server Configuration
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50
ALLOWED_AUDIO_EXTENSIONS=mp3,wav,m4a,ogg
ALLOWED_IMAGE_EXTENSIONS=jpg,jpeg,png

# Audio Processing
SILENCE_THRESHOLD=-40  # dB
MIN_SILENCE_LENGTH=500  # ms
SILENCE_KEEP=100  # ms

# Image Processing
FACE_DETECTION_CONFIDENCE=0.7
BLUR_KERNEL_SIZE=51

# Sarvam AI Configuration
SARVAM_API_BASE_URL=https://api.sarvam.ai  # Update if different
SARVAM_MODEL=saarika:v1  # Sarvam's speech recognition model
"""
    
    # Get the current directory
    current_dir = Path(__file__).parent
    env_file_path = current_dir / ".env"
    
    # Write the .env file with UTF-8 encoding
    with open(env_file_path, 'w', encoding='utf-8') as env_file:
        env_file.write(env_content)
    
    print(f".env file created successfully at: {env_file_path}")
    print("Your Sarvam AI API key has been configured")
    print("You can edit the .env file to adjust settings if needed")

if __name__ == "__main__":
    create_env_file()
