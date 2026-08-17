"""
Script to create dummy fixture files for testing
Creates minimal valid image and audio files for testing without external dependencies
"""
import os
from pathlib import Path
from PIL import Image
import struct

def create_dummy_jpg(output_path: str, size: tuple = (100, 100)):
    """Create a minimal valid JPEG file for testing"""
    # Create a simple image
    img = Image.new('RGB', size, color='red')
    img.save(output_path, 'JPEG', quality=95)
    print(f"Created dummy JPEG: {output_path}")

def create_dummy_wav(output_path: str, duration: float = 1.0, sample_rate: int = 44100):
    """Create a minimal valid WAV file for testing"""
    # WAV file header
    num_channels = 1
    bits_per_sample = 16
    bytes_per_sample = bits_per_sample // 8
    byte_rate = sample_rate * num_channels * bytes_per_sample
    block_align = num_channels * bytes_per_sample
    num_samples = int(duration * sample_rate)
    data_size = num_samples * block_align
    total_size = 36 + data_size
    
    with open(output_path, 'wb') as f:
        # RIFF header
        f.write(b'RIFF')
        f.write(struct.pack('<I', total_size))
        f.write(b'WAVE')
        
        # fmt chunk
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))  # PCM chunk size
        f.write(struct.pack('<H', 1))   # Audio format (PCM)
        f.write(struct.pack('<H', num_channels))
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', byte_rate))
        f.write(struct.pack('<H', block_align))
        f.write(struct.pack('<H', bits_per_sample))
        
        # data chunk
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        
        # Write silence (zeros)
        f.write(b'\x00' * data_size)
    
    print(f"Created dummy WAV: {output_path}")

def create_dummy_png(output_path: str, size: tuple = (100, 100)):
    """Create a minimal valid PNG file for testing"""
    img = Image.new('RGB', size, color='blue')
    img.save(output_path, 'PNG')
    print(f"Created dummy PNG: {output_path}")

def create_sideways_image(output_path: str):
    """Create an image that simulates a sideways photo"""
    # Create an image and rotate it to simulate sideways photo
    img = Image.new('RGB', (200, 100), color='green')
    # Rotate 90 degrees to simulate sideways photo
    sideways_img = img.rotate(90, expand=True)
    sideways_img.save(output_path, 'JPEG', quality=95)
    print(f"Created sideways JPEG: {output_path}")

if __name__ == "__main__":
    fixtures_dir = Path(__file__).parent
    
    # Create various test fixtures
    create_dummy_jpg(fixtures_dir / "test_image.jpg")
    create_dummy_png(fixtures_dir / "test_image.png")
    create_dummy_wav(fixtures_dir / "test_audio.wav")
    create_sideways_image(fixtures_dir / "test_sideways.jpg")
    
    print(f"\nAll fixture files created in: {fixtures_dir}")
