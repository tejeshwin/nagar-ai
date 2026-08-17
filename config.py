"""
Configuration management for Civic Complaint Intelligence Engine
Handles environment variables and API key management
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Keys
    openai_api_key: str = ""
    ai4bharat_api_key: str = ""
    openai_api_key_text: str = ""
    sarvam_api_key: str = ""
    sarvam_api_base_url: str = "https://api.sarvam.ai"
    sarvam_model: str = "saarika:v1"
    llama_api_key: str = ""
    llama_api_base_url: str = "https://api.llama-api.com"
    
    # Directory Configuration
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50
    
    # File Extensions
    allowed_audio_extensions: str = "mp3,wav,m4a,ogg"
    allowed_image_extensions: str = "jpg,jpeg,png"
    
    # Audio Processing Parameters
    silence_threshold: int = -40  # dB
    min_silence_length: int = 500  # ms
    silence_keep: int = 100  # ms
    
    # Image Processing Parameters
    face_detection_confidence: float = 0.7
    blur_kernel_size: int = 51
    
    @property
    def audio_extensions(self) -> List[str]:
        """Parse audio extensions into list"""
        return [ext.strip() for ext in self.allowed_audio_extensions.split(",")]
    
    @property
    def image_extensions(self) -> List[str]:
        """Parse image extensions into list"""
        return [ext.strip() for ext in self.allowed_image_extensions.split(",")]
    
    @property
    def upload_path(self) -> Path:
        """Get upload directory as Path object"""
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
