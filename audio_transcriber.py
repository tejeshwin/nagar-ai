"""
Audio Transcription Module - Robust Speech-to-Text
Handles audio transcription using Whisper/AI4Bharat with error handling for noisy inputs
Supports multiple languages including Tamil and Hindi
"""
import logging
import re
from typing import Optional, Dict, Union
import asyncio
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)

try:
    import whisper
except (ImportError, TypeError) as e:
    whisper = None
    logger.warning(f"Whisper import failed: {e}")

from openai import OpenAI
import requests
import base64


class AudioTranscriber:
    """
    Robust audio transcription with multiple API support and error handling
    Handles noisy audio, mixed languages, and various audio quality issues
    """
    
    def __init__(self):
        """Initialize transcriber with API clients"""
        self.openai_client = None
        self.whisper_model = None
        
        # Initialize OpenAI client if API key is available
        if settings.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=settings.openai_api_key)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Load local Whisper model as fallback
        try:
            if whisper:
                # Use base model for faster processing, can be upgraded to 'small' or 'medium'
                self.whisper_model = whisper.load_model("base")
                logger.info("Local Whisper model loaded")
            else:
                self.whisper_model = None
                logger.warning("Whisper module not available")
        except Exception as e:
            logger.warning(f"Failed to load Whisper model: {e}")
            self.whisper_model = None
        
        # Transcription parameters for noisy audio
        self.noisy_audio_params = {
            'temperature': 0.0,  # Lower temperature for more deterministic output
            'compression_ratio_threshold': 2.4,  # Filter out repetitive transcriptions
            'no_speech_threshold': 0.6,  # Threshold for detecting silence/noise
            'condition_on_previous_text': True,  # Maintain context
            'language': None,  # Auto-detect language
            'task': 'transcribe'
        }
    
    async def transcribe_audio(
        self, 
        audio_path: str, 
        language: Optional[str] = None,
        use_fallback: bool = True
    ) -> Dict:
        """
        Main entry point for audio transcription
        Tries multiple transcription methods with fallback
        
        Args:
            audio_path: Path to audio file to transcribe
            language: Optional language code (e.g., 'ta' for Tamil, 'hi' for Hindi)
            use_fallback: Whether to use fallback methods if primary fails
            
        Returns:
            Dictionary with transcription data and metadata
        """
        logger.info(f"Starting transcription for: {audio_path}")
        
        result = {
            'text': None,
            'language': None,
            'confidence': 0.0,
            'method': None,
            'duration': None,
            'error': None,
            'warnings': []
        }
        
        # Check if file exists
        if not Path(audio_path).exists():
            result['error'] = f"Audio file not found: {audio_path}"
            return result
        
        # Try OpenAI Whisper API first (most accurate)
        if self.openai_client:
            try:
                logger.info("Attempting OpenAI Whisper API transcription")
                transcription = await self._transcribe_with_openai(audio_path, language)
                if transcription and transcription.get('text'):
                    result.update(transcription)
                    result['method'] = 'openai_whisper'
                    logger.info("OpenAI Whisper transcription successful")
                    return result
            except Exception as e:
                warning = f"OpenAI Whisper API failed: {str(e)}"
                result['warnings'].append(warning)
                logger.warning(warning)
        
        # Try local Whisper model as fallback
        if self.whisper_model and whisper:
            try:
                logger.info("Attempting local Whisper transcription")
                transcription = await self._transcribe_with_whisper(audio_path, language)
                if transcription and transcription.get('text'):
                    result.update(transcription)
                    result['method'] = 'local_whisper'
                    logger.info("Local Whisper transcription successful")
                    return result
            except Exception as e:
                warning = f"Local Whisper failed: {str(e)}"
                result['warnings'].append(warning)
                logger.warning(warning)
        
        # Try Sarvam AI API (primary if configured)
        if settings.sarvam_api_key and use_fallback:
            try:
                logger.info("Attempting Sarvam AI API transcription")
                transcription = await self._transcribe_with_sarvam(audio_path, language)
                if transcription and transcription.get('text'):
                    result.update(transcription)
                    result['method'] = 'sarvam'
                    logger.info("Sarvam AI API transcription successful")
                    return result
            except Exception as e:
                warning = f"Sarvam AI API failed: {str(e)}"
                result['warnings'].append(warning)
                logger.warning(warning)
        
        # Try AI4Bharat API for Indic languages
        if settings.ai4bharat_api_key and use_fallback:
            try:
                logger.info("Attempting AI4Bharat API transcription")
                transcription = await self._transcribe_with_ai4bharat(audio_path, language)
                if transcription and transcription.get('text'):
                    result.update(transcription)
                    result['method'] = 'ai4bharat'
                    logger.info("AI4Bharat transcription successful")
                    return result
            except Exception as e:
                warning = f"AI4Bharat API failed: {str(e)}"
                result['warnings'].append(warning)
                logger.warning(warning)
        
        # All methods failed
        result['error'] = "All transcription methods failed"
        logger.error("All transcription methods failed")
        return result
    
    async def _transcribe_with_openai(
        self, 
        audio_path: str, 
        language: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Transcribe using OpenAI Whisper API
        Handles noisy audio with optimized parameters
        """
        try:
            with open(audio_path, 'rb') as audio_file:
                # Use Whisper API with parameters for noisy audio
                response = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,  # None for auto-detection
                    response_format="verbose_json",
                    temperature=0.0,  # Lower temperature for noisy audio
                    timestamp_granularities=["word"]  # Get word-level timestamps
                )
            
            return {
                'text': response.text,
                'language': response.language,
                'confidence': 0.9,  # OpenAI Whisper is generally reliable
                'duration': response.duration
            }
            
        except Exception as e:
            logger.error(f"OpenAI Whisper API error: {e}")
            raise
    
    async def _transcribe_with_whisper(
        self, 
        audio_path: str, 
        language: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Transcribe using local Whisper model
        Implements robust handling for noisy audio
        """
        try:
            # Run transcription in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Prepare transcription options
            options = {
                'fp16': False,  # Use FP32 for better accuracy
                'language': language if language else None,  # Auto-detect if None
                **self.noisy_audio_params
            }
            
            # Perform transcription
            result = await loop.run_in_executor(
                None, 
                lambda: self.whisper_model.transcribe(
                    audio_path, 
                    **options
                )
            )
            
            # Extract relevant information
            text = result.get('text', '').strip()
            detected_language = result.get('language', 'unknown')
            
            # Validate transcription quality
            if not text or len(text) < 3:
                raise ValueError("Transcription too short or empty")
            
            # Check for repetitive/low-quality output
            if result.get('compression_ratio_threshold'):
                # This is handled internally by Whisper
                pass
            
            return {
                'text': text,
                'language': detected_language,
                'confidence': 0.8,  # Local model slightly less confident
                'duration': result.get('segments', [{}])[-1].get('end', 0) if result.get('segments') else None
            }
            
        except Exception as e:
            logger.error(f"Local Whisper error: {e}")
            raise
    
    async def _transcribe_with_ai4bharat(
        self, 
        audio_path: str, 
        language: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Transcribe using AI4Bharat API (specialized for Indic languages)
        Good fallback for Tamil, Hindi, and other Indian languages
        """
        try:
            # AI4Bharat API endpoint (example - replace with actual endpoint)
            api_url = "https://ai4bharat.org/api/transcribe"
            
            # Prepare request
            files = {'audio': open(audio_path, 'rb')}
            data = {
                'language': language if language else 'auto',
                'model': 'whisper-medium'  # Or appropriate AI4Bharat model
            }
            headers = {'Authorization': f'Bearer {settings.ai4bharat_api_key}'}
            
            # Make API call
            response = await asyncio.to_thread(
                requests.post,
                api_url,
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'text': result.get('transcription', ''),
                    'language': result.get('language', language),
                    'confidence': 0.75,  # Moderate confidence for API fallback
                    'duration': result.get('duration')
                }
            else:
                raise Exception(f"AI4Bharat API returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"AI4Bharat API error: {e}")
            raise
    
    async def _transcribe_with_sarvam(
        self, 
        audio_path: str, 
        language: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Transcribe using Sarvam AI API
        Sarvam AI specializes in Indic languages like Tamil, Hindi, etc.
        """
        try:
            # Read audio file
            with open(audio_path, 'rb') as audio_file:
                audio_content = audio_file.read()
            
            # Sarvam AI API endpoint for speech recognition
            api_url = f"{settings.sarvam_api_base_url}/speech/speech-to-text"
            
            headers = {
                'API-KEY': settings.sarvam_api_key,
                'Content-Type': 'application/json'
            }
            
            # Prepare request data for Sarvam AI
            files = {
                'file': (Path(audio_path).name, audio_content, 'audio/wav')
            }
            
            data = {
                'model': settings.sarvam_model,
                'language_code': language if language else 'auto'
            }
            
            logger.info(f"Sending audio to Sarvam AI: {audio_path}")
            
            # Make API call
            response = await asyncio.to_thread(
                requests.post,
                api_url,
                files=files,
                data=data,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Parse Sarvam AI response format
                transcription_text = result.get('transcript', result.get('text', ''))
                detected_language = result.get('language_code', language)
                
                return {
                    'text': transcription_text,
                    'language': detected_language,
                    'confidence': 0.90,  # Sarvam AI provides high accuracy for Indic languages
                    'duration': result.get('duration')
                }
            else:
                error_msg = f"Sarvam AI API returned status {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f": {error_detail.get('error', response.text)}"
                except:
                    error_msg += f": {response.text}"
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Sarvam AI API error: {e}")
            raise
    
    def detect_language(self, text: str) -> str:
        """
        Simple language detection from transcribed text
        Can be enhanced with proper language detection library
        """
        # Basic heuristics for common Indian languages
        tamil_chars = set('அஆஇஈஉஊஎஏஐஒஓஔகஙசஜஞடணதநபமயரறலளழவஷஸஹ')
        hindi_chars = set('अआइईउऊएऐओऔकखगघचछजझटठडढणतथदधनपफबभमयरलवषसह')
        
        text_chars = set(text)
        
        if text_chars & tamil_chars:
            return 'ta'  # Tamil
        elif text_chars & hindi_chars:
            return 'hi'  # Hindi
        else:
            return 'en'  # Default to English
    
    async def enhance_transcription_quality(
        self, 
        audio_path: str, 
        transcription: str
    ) -> str:
        """
        Enhance transcription quality using post-processing
        Removes common artifacts and improves readability
        """
        try:
            # Remove common transcription artifacts
            artifacts = [
                r'\[.*?\]',  # Remove bracketed text
                r'\(.*?\)',  # Remove parenthetical text
                r'\{.*?\}',  # Remove braced text
                r'\s+',  # Normalize whitespace
                r'^\s+|\s+$',  # Trim leading/trailing whitespace
            ]
            
            enhanced_text = transcription
            for artifact in artifacts:
                enhanced_text = re.sub(artifact, ' ', enhanced_text)
            
            # Clean up multiple spaces
            enhanced_text = ' '.join(enhanced_text.split())
            
            return enhanced_text.strip()
            
        except Exception as e:
            logger.warning(f"Transcription enhancement failed: {e}")
            return transcription


# Global audio transcriber instance
audio_transcriber = AudioTranscriber()
