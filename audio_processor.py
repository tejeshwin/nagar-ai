"""
Audio Processing Module - Edge-Processed Audio Compression
Implements lightweight audio compression and silence trimming for cost-effective transcription
"""
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import logging

from pydub import AudioSegment
from pydub.silence import split_on_silence
import aiofiles

from config import settings

logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    Handles audio compression and preprocessing before transcription
    Implements edge-processing to reduce API costs and improve transcription accuracy
    """
    
    def __init__(self):
        """Initialize audio processor with configuration"""
        self.silence_threshold = settings.silence_threshold
        self.min_silence_length = settings.min_silence_length
        self.silence_keep = settings.silence_keep
        self.supported_formats = ['mp3', 'wav', 'm4a', 'ogg', 'flac']
    
    async def process_audio_file(
        self, 
        file_path: str, 
        output_format: str = 'mp3'
    ) -> Tuple[str, dict]:
        """
        Main entry point for audio processing
        Applies compression, silence trimming, and format conversion
        
        Args:
            file_path: Path to input audio file
            output_format: Desired output format (default: mp3)
            
        Returns:
            Tuple of (processed_file_path, metadata_dict)
        """
        try:
            logger.info(f"Processing audio file: {file_path}")
            
            # Load audio file
            audio_segment = await self._load_audio(file_path)
            if audio_segment is None:
                raise ValueError("Failed to load audio file")
            
            original_duration = len(audio_segment) / 1000  # Convert to seconds
            original_size = os.path.getsize(file_path)
            
            # Apply processing pipeline
            processed_audio = await self._apply_processing_pipeline(audio_segment)
            
            # Save processed audio
            processed_path = await self._save_processed_audio(
                processed_audio, 
                file_path, 
                output_format
            )
            
            # Calculate compression stats
            processed_size = os.path.getsize(processed_path)
            processed_duration = len(processed_audio) / 1000
            
            metadata = {
                'original_duration': original_duration,
                'processed_duration': processed_duration,
                'original_size': original_size,
                'processed_size': processed_size,
                'compression_ratio': round(original_size / processed_size, 2),
                'duration_reduction': round((1 - processed_duration / original_duration) * 100, 2),
                'format': output_format
            }
            
            logger.info(f"Audio processing complete. Compression ratio: {metadata['compression_ratio']}x")
            return processed_path, metadata
            
        except Exception as e:
            logger.error(f"Error processing audio file: {e}")
            raise
    
    async def _load_audio(self, file_path: str) -> Optional[AudioSegment]:
        """
        Load audio file with format detection
        Handles various audio formats and error cases
        """
        try:
            file_ext = Path(file_path).suffix.lower().lstrip('.')
            
            if file_ext not in self.supported_formats:
                logger.warning(f"Unsupported format: {file_ext}, attempting conversion")
            
            # Try loading with format detection
            audio = AudioSegment.from_file(file_path)
            
            # Normalize audio to standard volume
            audio = self._normalize_audio(audio)
            
            return audio
            
        except Exception as e:
            logger.error(f"Failed to load audio file {file_path}: {e}")
            return None
    
    def _normalize_audio(self, audio: AudioSegment) -> AudioSegment:
        """
        Normalize audio to standard volume level
        Helps with consistent transcription quality
        """
        try:
            # Calculate target dBFS
            target_dBFS = -20.0
            change_in_dBFS = target_dBFS - audio.dBFS
            
            # Apply normalization
            normalized_audio = audio.apply_gain(change_in_dBFS)
            return normalized_audio
            
        except Exception as e:
            logger.warning(f"Audio normalization failed: {e}, using original")
            return audio
    
    async def _apply_processing_pipeline(self, audio: AudioSegment) -> AudioSegment:
        """
        Apply the complete audio processing pipeline
        1. Trim silence from beginning and end
        2. Remove long silence gaps in the middle
        3. Compress audio quality
        """
        try:
            # Step 1: Trim leading/trailing silence
            audio = self._trim_silence(audio)
            
            # Step 2: Split on silence and remove very long gaps
            audio_chunks = split_on_silence(
                audio,
                min_silence_len=self.min_silence_length,
                silence_thresh=self.silence_threshold,
                keep_silence=self.silence_keep
            )
            
            # Rejoin chunks (this removes long silence gaps)
            if audio_chunks:
                processed_audio = audio_chunks[0]
                for chunk in audio_chunks[1:]:
                    processed_audio += chunk
            else:
                # If splitting removed everything, return original trimmed audio
                processed_audio = audio
            
            # Step 3: Compress audio quality for API efficiency
            processed_audio = self._compress_audio(processed_audio)
            
            return processed_audio
            
        except Exception as e:
            logger.warning(f"Processing pipeline failed: {e}, returning original audio")
            return audio
    
    def _trim_silence(self, audio: AudioSegment) -> AudioSegment:
        """
        Trim silence from beginning and end of audio
        """
        try:
            # Trim leading silence
            start_trim = self._detect_leading_silence(audio)
            end_trim = self._detect_leading_silence(audio.reverse())
            
            duration = len(audio)
            trimmed_audio = audio[start_trim:duration - end_trim]
            
            return trimmed_audio
            
        except Exception as e:
            logger.warning(f"Silence trimming failed: {e}")
            return audio
    
    def _detect_leading_silence(self, audio: AudioSegment) -> int:
        """
        Detect the length of leading silence in audio
        """
        try:
            silence_threshold = self.silence_threshold
            chunk_size = 10  # ms
            
            for i in range(0, len(audio), chunk_size):
                chunk = audio[i:i + chunk_size]
                if chunk.dBFS < silence_threshold:
                    continue
                else:
                    return i
            
            return len(audio)  # Entire audio is silence
            
        except Exception:
            return 0
    
    def _compress_audio(self, audio: AudioSegment) -> AudioSegment:
        """
        Compress audio to reduce file size while maintaining quality
        Uses appropriate bitrate for speech
        """
        try:
            # For speech, 64kbps is usually sufficient
            # Export with compression parameters
            return audio
            
        except Exception as e:
            logger.warning(f"Audio compression failed: {e}")
            return audio
    
    async def _save_processed_audio(
        self, 
        audio: AudioSegment, 
        original_path: str, 
        output_format: str
    ) -> str:
        """
        Save processed audio to disk
        """
        try:
            # Create output filename
            original_path_obj = Path(original_path)
            output_filename = f"processed_{original_path_obj.stem}.{output_format}"
            output_path = settings.upload_path / output_filename
            
            # Export with appropriate parameters
            if output_format == 'mp3':
                audio.export(
                    str(output_path),
                    format='mp3',
                    bitrate='64k',
                    parameters=['-q:a', '2']  # Quality setting
                )
            elif output_format == 'wav':
                audio.export(str(output_path), format='wav')
            else:
                audio.export(str(output_path), format=output_format)
            
            logger.info(f"Saved processed audio to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to save processed audio: {e}")
            raise


# Global audio processor instance
audio_processor = AudioProcessor()
