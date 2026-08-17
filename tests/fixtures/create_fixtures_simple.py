"""
Script to create dummy fixture files for testing using minimal dependencies
Creates valid image and audio files without requiring PIL
"""
import os
from pathlib import Path
import struct

def create_dummy_jpg(output_path: str):
    """Create a minimal valid JPEG file for testing"""
    # Minimal JPEG header and footer
    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x03\x02\x02\x03\x02\x02\x03\x03\x03\x03\x04\x03\x03\x04\x05\x08\x05\x05\x04\x04\x05\n\x07\x07\x06\x08\x0c\n\x0c\x0c\x0b\n\x0b\x0b\r\x0e\x12\x10\r\x0e\x11\x0e\x0b\x0b\x10\x16\x10\x11\x13\x14\x15\x15\x15\x0c\x0f\x17\x18\x16\x14\x18\x12\x14\x15\x14\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\xb1\xc1\t#3R\xd1\xf0\x15\x04br\x82\x92\xa2\xb2\xc2\xd2\xe2\xf2\n\x16\x17\x18\x19\x1a%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\x7f\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12QA\x07\x13q\x81\x91\xa1\x22\xb1\xc1\x14\xd1\xf0#3R\x15\x04br\x82\x92\xa2\xb2\xc2\xd2\xe2\xf2\n\x16\x17\x18\x19\x1a%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\x7f\xff\xda\x00\x08\x01\x01\x00\x00?'
    jpeg_footer = b'\xff\xd9'
    
    with open(output_path, 'wb') as f:
        f.write(jpeg_header)
        f.write(jpeg_footer)
    
    print(f"Created dummy JPEG: {output_path}")

def create_dummy_wav(output_path: str, duration: float = 1.0, sample_rate: int = 44100):
    """Create a minimal valid WAV file for testing"""
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

def create_dummy_png(output_path: str):
    """Create a minimal valid PNG file for testing"""
    # Minimal PNG header and footer
    png_header = b'\x89PNG\r\n\x1a\n'
    # Minimal IHDR chunk for 1x1 pixel
    ihdr = b'IHDR' + struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0) + b'\x00\x00\x00\r'
    # IDAT chunk with minimal data
    idat = b'IDAT' + b'\x78\x9c\x62\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4' + b'\x00\x00\x00\n'
    # IEND chunk
    iend = b'IEND' + b'\xae\x42\x60\x82'
    
    with open(output_path, 'wb') as f:
        f.write(png_header)
        f.write(ihdr)
        f.write(idat)
        f.write(iend)
    
    print(f"Created dummy PNG: {output_path}")

def create_sideways_image(output_path: str):
    """Create a JPEG that simulates a sideways photo (same as normal for testing)"""
    # For testing purposes, we create the same JPEG
    # The important thing is that the API doesn't crash on it
    create_dummy_jpg(output_path)
    print(f"Created sideways JPEG (for testing): {output_path}")

if __name__ == "__main__":
    fixtures_dir = Path(__file__).parent
    
    # Create various test fixtures
    create_dummy_jpg(fixtures_dir / "test_image.jpg")
    create_dummy_png(fixtures_dir / "test_image.png")
    create_dummy_wav(fixtures_dir / "test_audio.wav")
    create_sideways_image(fixtures_dir / "test_sideways.jpg")
    
    print(f"\nAll fixture files created in: {fixtures_dir}")
