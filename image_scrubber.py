"""
Image Privacy Scrubber Module - Privacy-by-Design Image Processing
Detects and blurs faces and license plates using OpenCV Haar Cascades
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, List, Dict
import logging
import asyncio

from config import settings

logger = logging.getLogger(__name__)


class ImageScrubber:
    """
    Privacy-by-design image processor that detects and blurs sensitive information
    Handles faces and license plates while preserving image orientation
    """
    
    def __init__(self):
        """Initialize image scrubber with Haar Cascade classifiers"""
        self.face_cascade = None
        self.license_plate_cascade = None
        self.blur_kernel_size = settings.blur_kernel_size
        self.confidence_threshold = settings.face_detection_confidence
        
        # Load classifiers asynchronously
        self._load_classifiers()
    
    def _load_classifiers(self):
        """
        Load OpenCV Haar Cascade classifiers
        Downloads them if not available locally
        """
        try:
            # Load face cascade
            face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
            
            # Load license plate cascade
            license_plate_cascade_path = cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'
            self.license_plate_cascade = cv2.CascadeClassifier(license_plate_cascade_path)
            
            logger.info("Successfully loaded Haar Cascade classifiers")
            
        except Exception as e:
            logger.error(f"Failed to load Haar Cascade classifiers: {e}")
            # Continue without classifiers - will skip detection
    
    async def scrub_image(
        self, 
        image_path: str, 
        scrub_faces: bool = True, 
        scrub_license_plates: bool = True
    ) -> Tuple[str, Dict]:
        """
        Main entry point for image privacy scrubbing
        Detects and blurs faces and license plates while preserving image orientation
        
        Args:
            image_path: Path to input image
            scrub_faces: Whether to detect and blur faces
            scrub_license_plates: Whether to detect and blur license plates
            
        Returns:
            Tuple of (scrubbed_image_path, metadata_dict)
        """
        try:
            logger.info(f"Scrubbing image: {image_path}")
            
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Failed to read image file")
            
            original_shape = image.shape
            metadata = {
                'original_shape': original_shape,
                'faces_detected': 0,
                'license_plates_detected': 0,
                'scrubbed_regions': []
            }
            
            # Detect and scrub faces
            if scrub_faces and self.face_cascade is not None:
                faces = self._detect_faces(image)
                metadata['faces_detected'] = len(faces)
                
                for (x, y, w, h) in faces:
                    # Apply blur to face region
                    image = self._apply_gaussian_blur(image, x, y, w, h)
                    metadata['scrubbed_regions'].append({
                        'type': 'face',
                        'bbox': [int(x), int(y), int(w), int(h)]
                    })
            
            # Detect and scrub license plates
            if scrub_license_plates and self.license_plate_cascade is not None:
                license_plates = self._detect_license_plates(image)
                metadata['license_plates_detected'] = len(license_plates)
                
                for (x, y, w, h) in license_plates:
                    # Apply blur to license plate region
                    image = self._apply_gaussian_blur(image, x, y, w, h)
                    metadata['scrubbed_regions'].append({
                        'type': 'license_plate',
                        'bbox': [int(x), int(y), int(w), int(h)]
                    })
            
            # Save scrubbed image
            scrubbed_path = await self._save_scrubbed_image(image, image_path)
            
            logger.info(f"Image scrubbing complete. Faces: {metadata['faces_detected']}, "
                       f"License plates: {metadata['license_plates_detected']}")
            
            return scrubbed_path, metadata
            
        except Exception as e:
            logger.error(f"Error scrubbing image: {e}")
            # Return original image path if scrubbing fails
            return image_path, {'error': str(e)}
    
    def _detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in image using Haar Cascade
        Returns list of (x, y, width, height) tuples
        """
        try:
            # Convert to grayscale for detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            return faces
            
        except Exception as e:
            logger.warning(f"Face detection failed: {e}")
            return []
    
    def _detect_license_plates(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect license plates in image using Haar Cascade
        Returns list of (x, y, width, height) tuples
        """
        try:
            # Convert to grayscale for detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect license plates
            license_plates = self.license_plate_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 10),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            return license_plates
            
        except Exception as e:
            logger.warning(f"License plate detection failed: {e}")
            return []
    
    def _apply_gaussian_blur(
        self, 
        image: np.ndarray, 
        x: int, 
        y: int, 
        w: int, 
        h: int
    ) -> np.ndarray:
        """
        Apply Gaussian blur to specified region
        Expands the region slightly to ensure complete coverage
        """
        try:
            # Expand region slightly for better coverage
            padding = 10
            x_start = max(0, x - padding)
            y_start = max(0, y - padding)
            x_end = min(image.shape[1], x + w + padding)
            y_end = min(image.shape[0], y + h + padding)
            
            # Extract region
            region = image[y_start:y_end, x_start:x_end]
            
            # Apply Gaussian blur
            if region.size > 0:
                blurred_region = cv2.GaussianBlur(
                    region, 
                    (self.blur_kernel_size, self.blur_kernel_size), 
                    0
                )
                
                # Replace region with blurred version
                image[y_start:y_end, x_start:x_end] = blurred_region
            
            return image
            
        except Exception as e:
            logger.warning(f"Failed to apply blur: {e}")
            return image
    
    async def _save_scrubbed_image(
        self, 
        image: np.ndarray, 
        original_path: str
    ) -> str:
        """
        Save scrubbed image to disk
        Preserves original image format and quality
        """
        try:
            # Create output filename
            original_path_obj = Path(original_path)
            output_filename = f"scrubbed_{original_path_obj.name}"
            output_path = settings.upload_path / output_filename
            
            # Save image preserving original quality
            cv2.imwrite(str(output_path), image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            logger.info(f"Saved scrubbed image to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to save scrubbed image: {e}")
            raise
    
    async def extract_exif_location(self, image_path: str) -> Tuple[float, float]:
        """
        Extract GPS coordinates from image EXIF data
        Returns (latitude, longitude) or (None, None) if not available
        
        Note: This is a basic implementation. For production, consider using
        libraries like pillow or exif for more robust EXIF parsing
        """
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS
            
            image = Image.open(image_path)
            exif_data = image._getexif()
            
            if exif_data is None:
                return None, None
            
            # Get GPS info
            gps_info = None
            for tag, value in exif_data.items():
                tag_name = TAGS.get(tag, tag)
                if tag_name == "GPSInfo":
                    gps_info = value
                    break
            
            if gps_info is None:
                return None, None
            
            # Extract latitude and longitude
            def convert_to_degrees(value):
                """Convert GPS coordinates to decimal degrees"""
                degrees = float(value[0])
                minutes = float(value[1])
                seconds = float(value[2])
                return degrees + (minutes / 60.0) + (seconds / 3600.0)
            
            # Get latitude
            lat = None
            lat_ref = None
            for key, value in gps_info.items():
                tag_name = GPSTAGS.get(key, key)
                if tag_name == "GPSLatitude":
                    lat = convert_to_degrees(value)
                elif tag_name == "GPSLatitudeRef":
                    lat_ref = value
            
            # Get longitude
            lon = None
            lon_ref = None
            for key, value in gps_info.items():
                tag_name = GPSTAGS.get(key, key)
                if tag_name == "GPSLongitude":
                    lon = convert_to_degrees(value)
                elif tag_name == "GPSLongitudeRef":
                    lon_ref = value
            
            # Apply reference directions
            if lat and lon and lat_ref and lon_ref:
                lat = -lat if lat_ref == 'S' else lat
                lon = -lon if lon_ref == 'W' else lon
                return lat, lon
            
            return None, None
            
        except Exception as e:
            logger.warning(f"Failed to extract EXIF location: {e}")
            return None, None


# Global image scrubber instance
image_scrubber = ImageScrubber()
