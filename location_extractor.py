"""
Location Extraction Module - Interactive Missing-Data Fallback
Extracts location from GPS coordinates, text mentions, or EXIF data
Implements conversational fallback when location cannot be determined
"""
import re
import logging
from typing import Tuple, Optional, Dict, List
from pathlib import Path
import asyncio

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from config import settings
from image_scrubber import image_scrubber

logger = logging.getLogger(__name__)


class LocationExtractor:
    """
    Multi-source location extraction with intelligent fallback
    Handles GPS coordinates, text-based location mentions, and EXIF data
    """
    
    def __init__(self):
        """Initialize location extractor with geocoding service"""
        self.geolocator = Nominatim(user_agent="civic_complaint_engine")
        
        # Regex patterns for location mentions in text
        self.location_patterns = [
            # Indian address patterns
            r'(?:at|near|in|on|from)\s+([A-Za-z\s]+(?:Street|Road|Lane|Avenue|Nagar|Colony|Area|Sector|Phase|Layout|Extension|Main|Cross|Circle|Square|Market|Complex|Building)[,\s]*[A-Za-z\s0-9]*)',
            r'([A-Za-z\s]+(?:District|Taluk|Tehsil|Mandal|State)[,\s]*[A-Za-z\s]*)',
            # Pin code patterns
            r'(\d{6})',  # Indian pin codes
            # General location patterns
            r'(?:location|gps|coordinates?|where)\s*[:=]\s*([A-Za-z0-9\s,.-]+)',
            # Street addresses
            r'(\d+\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Lane|Ln|Ave|Avenue)[,\s]*[A-Za-z\s0-9]*)',
        ]
        
        # City names for common Indian cities (expandable)
        self.indian_cities = [
            'Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad',
            'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow', 'Kanpur', 'Nagpur',
            'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Pimpri', 'Patna',
            'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra', 'Nashik', 'Ranchi',
            'Faridabad', 'Meerut', 'Rajkot', 'Varanasi', 'Srinagar', 'Aurangabad',
            'Dhanbad', 'Amritsar', 'Navi Mumbai', 'Allahabad', 'Howrah', 'Jabalpur',
            'Gwalior', 'Vijayawada', 'Jodhpur', 'Madurai', 'Raipur', 'Kota',
            'Guwahati', 'Chandigarh', 'Solapur', 'Hubli', 'Mysore', 'Tiruchirappalli',
            'Bareilly', 'Aligarh', 'Tiruppur', 'Gurgaon', 'Moradabad', 'Jalandhar',
            'Bhubaneswar', 'Salem', 'Warangal', 'Mira-Bhayandar', 'Thiruvananthapuram',
            'Bhiwandi', 'Saharanpur', 'Guntur', 'Amravati', 'Bikaner', 'Noida',
            'Jamshedpur', 'Bhilai', 'Cuttack', 'Firozabad', 'Kochi', 'Nellore',
            'Bhavnagar', 'Dehradun', 'Durgapur', 'Asansol', 'Rourkela', 'Nanded',
            'Kolhapur', 'Ajmer', 'Akola', 'Gulbarga', 'Jamnagar', 'Ujjain',
            'Loni', 'Siliguri', 'Jhansi', 'Ulhasnagar', 'Jammu', 'Sangli-Miraj & Kupwad',
            'Mangalore', 'Erode', 'Belgaum', 'Ambattur', 'Tirunelveli', 'Malegaon',
            'Gaya', 'Jalgaon', 'Udaipur', 'Maheshtala', 'Tirupur', 'Davanagere',
            'Kozhikode', 'Akbarpur', 'Rajpur Sonarpur', 'Bokaro', 'South Dumdum',
            'Bellary', 'Patiala', 'Gopalpur', 'Agartala', 'Bhagalpur', 'Muzaffarnagar',
            'Latur', 'Dhule', 'Rohtak', 'Korba', 'Bhilwara', 'Berhampur',
            'Muzaffarpur', 'Ahmednagar', 'Mathura', 'Kollam', 'Avadi', 'Kadapa',
            'Kamarhati', 'Sambalpur', 'Bilaspur', 'Shahjahanpur', 'Satara', 'Bijapur',
            'Rampur', 'Shivamogga', 'Chandrapur', 'Junagadh', 'Thrissur', 'Alwar',
            'Bardhaman', 'Kulti', 'Nizamabad', 'Parbhani', 'Tumkur', 'Khammam',
            'Ozhukarai', 'Bihar Sharif', 'Panipat', 'Darbhanga', 'Bally', 'Aizawl',
            'Dewas', 'Ichalkaranji', 'Karnal', 'Bathinda', 'Jalna', 'Eluru',
            'Barasat', 'Kirari Suleman Nagar', 'Purnia', 'Satna', 'Mau', 'Sonipat',
            'Farrukhabad', 'Sagar', 'Rourkela', 'Durg', 'Imphal', 'Ratlam',
            'Hapur', 'Arrah', 'Anantapur', 'Karimnagar', 'Etawah', 'Ambarnath',
            'North Dumdum', 'Bharatpur', 'Begusarai', 'New Delhi', 'Gandhidham',
            'Baranagar', 'Tirupati', 'Puducherry', 'Sikar', 'Thoothukudi', 'Rewa',
            'Mirzapur', 'Raichur', 'Pali', 'Ramagundam', 'Silchar', 'Haridwar',
            'Vijayanagaram', 'Tenali', 'Nagercoil', 'Sri Ganganagar', 'Karawal Nagar',
            'Mango', 'Thanjavur', 'Bulandshahr', 'Uluberia', 'Murwara', 'Sambhal',
            'Singrauli', 'Nadiad', 'Secunderabad', 'Naihati', 'Yamunanagar', 'Bidhan Nagar',
            'Pallavaram', 'Bidar', 'Munger', 'Panchkula', 'Burhanpur', 'Raurkela',
            'Kharagpur', 'Dindigul', 'Gandhinagar', 'Hospet', 'Nangloi Jat', 'Malda',
            'Ongole', 'Deoghar', 'Chapra', 'Haldia', 'Khandwa', 'Nandyal',
            'Morena', 'Amroha', 'Anand', 'Bhind', 'Bhalswa Jahangir Pur', 'Madhyamgram',
            'Bhiwani', 'Berhampore', 'Ambala', 'Morbi', 'Fatehpur', 'Raebareli',
            'Khora', 'Chittoor', 'Bhusawal', 'Orai', 'Bahraich', 'Phusro',
            'Vellore', 'Mehsana', 'Raiganj', 'Sirsa', 'Danapur', 'Serampore',
            'Sultan Pur Majra', 'Guna', 'Jaunpur', 'Panvel', 'Shivpuri', 'Surendranagar Dudhrej',
            'Unnao', 'Chinsurah', 'Alappuzha', 'Kottayam', 'Machilipatnam', 'Shimla',
            'Adoni', 'Udupi', 'Katihar', 'Proddatur', 'Mahbubnagar', 'Saharsa',
            'Dibrugarh', 'Jorhat', 'Hazaribagh', 'Hindupur', 'Nagaon', 'Hajipur'
        ]
    
    async def extract_location(
        self, 
        text: Optional[str] = None,
        image_path: Optional[str] = None,
        gps_coordinates: Optional[Tuple[float, float]] = None,
        enable_fallback: bool = True
    ) -> Dict:
        """
        Main entry point for location extraction
        Tries multiple sources in priority order with fallback
        
        Args:
            text: Text content that might contain location mentions
            image_path: Path to image with potential EXIF GPS data
            gps_coordinates: Direct GPS coordinates as (latitude, longitude)
            enable_fallback: Whether to enable conversational fallback
            
        Returns:
            Dictionary with location data and metadata
        """
        logger.info("Starting location extraction")
        
        result = {
            'coordinates': None,  # [latitude, longitude]
            'source': None,  # 'gps', 'exif', 'text', 'fallback'
            'confidence': 0.0,
            'address': None,
            'requires_user_input': False,
            'fallback_message': None
        }
        
        # Priority 1: Direct GPS coordinates
        if gps_coordinates:
            result['coordinates'] = list(gps_coordinates)
            result['source'] = 'gps'
            result['confidence'] = 1.0
            result['address'] = await self._reverse_geocode(gps_coordinates)
            logger.info(f"Location found via GPS: {gps_coordinates}")
            return result
        
        # Priority 2: EXIF data from image
        if image_path:
            exif_coords = await image_scrubber.extract_exif_location(image_path)
            if exif_coords[0] is not None and exif_coords[1] is not None:
                result['coordinates'] = list(exif_coords)
                result['source'] = 'exif'
                result['confidence'] = 0.9
                result['address'] = await self._reverse_geocode(exif_coords)
                logger.info(f"Location found via EXIF: {exif_coords}")
                return result
        
        # Priority 3: Text-based location extraction
        if text:
            text_location = await self._extract_from_text(text)
            if text_location:
                result.update(text_location)
                logger.info(f"Location found via text: {text_location}")
                return result
        
        # Priority 4: Conversational fallback
        if enable_fallback:
            result['requires_user_input'] = True
            result['fallback_message'] = self._generate_fallback_message()
            logger.info("Location not found, triggering fallback")
        
        return result
    
    async def _extract_from_text(self, text: str) -> Optional[Dict]:
        """
        Extract location from text using pattern matching and geocoding
        """
        try:
            text = text.lower()
            location_data = None
            max_confidence = 0.0
            
            # Check for Indian city names
            for city in self.indian_cities:
                if city.lower() in text:
                    confidence = 0.7
                    if confidence > max_confidence:
                        coordinates = await self._geocode(city)
                        if coordinates:
                            location_data = {
                                'coordinates': list(coordinates),
                                'source': 'text',
                                'confidence': confidence,
                                'address': city
                            }
                            max_confidence = confidence
            
            # Try regex patterns
            for pattern in self.location_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    location_text = match.group(1).strip()
                    if len(location_text) > 3:  # Minimum length threshold
                        coordinates = await self._geocode(location_text)
                        if coordinates:
                            confidence = 0.6
                            if confidence > max_confidence:
                                location_data = {
                                    'coordinates': list(coordinates),
                                    'source': 'text',
                                    'confidence': confidence,
                                    'address': location_text
                                }
                                max_confidence = confidence
            
            return location_data
            
        except Exception as e:
            logger.warning(f"Text-based location extraction failed: {e}")
            return None
    
    async def _geocode(self, location_text: str) -> Optional[Tuple[float, float]]:
        """
        Convert location text to coordinates using geocoding
        """
        try:
            # Add ", India" to improve accuracy for Indian locations
            search_text = f"{location_text}, India"
            
            location = self.geolocator.geocode(search_text, timeout=10)
            if location:
                return (location.latitude, location.longitude)
            
            # Try without "India" suffix
            location = self.geolocator.geocode(location_text, timeout=10)
            if location:
                return (location.latitude, location.longitude)
            
            return None
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Geocoding failed for '{location_text}': {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected geocoding error: {e}")
            return None
    
    async def _reverse_geocode(self, coordinates: Tuple[float, float]) -> Optional[str]:
        """
        Convert coordinates to readable address
        """
        try:
            location = self.geolocator.reverse(
                f"{coordinates[0]}, {coordinates[1]}",
                timeout=10
            )
            if location:
                return location.address
            return None
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Reverse geocoding failed: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected reverse geocoding error: {e}")
            return None
    
    def _generate_fallback_message(self) -> str:
        """
        Generate conversational fallback message for missing location
        """
        return (
            "I see the issue, but I need the location to report it. "
            "Can you drop a GPS pin or type the street name?"
        )
    
    async def process_user_location_response(
        self, 
        user_response: str
    ) -> Dict:
        """
        Process user's response to location fallback request
        Handles GPS coordinates or text-based location input
        """
        logger.info(f"Processing user location response: {user_response}")
        
        result = {
            'coordinates': None,
            'source': 'user_input',
            'confidence': 0.0,
            'address': None,
            'requires_user_input': False,
            'fallback_message': None
        }
        
        # Try to parse GPS coordinates
        gps_match = re.search(
            r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)',
            user_response
        )
        if gps_match:
            try:
                lat = float(gps_match.group(1))
                lon = float(gps_match.group(2))
                
                # Validate coordinate ranges
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    result['coordinates'] = [lat, lon]
                    result['confidence'] = 1.0
                    result['address'] = await self._reverse_geocode((lat, lon))
                    logger.info(f"User provided GPS coordinates: {lat}, {lon}")
                    return result
            except ValueError:
                pass
        
        # Try text-based location
        text_location = await self._extract_from_text(user_response)
        if text_location:
            result.update(text_location)
            result['source'] = 'user_input'
            logger.info(f"User provided text location: {text_location}")
            return result
        
        # Still no location - ask again
        result['requires_user_input'] = True
        result['fallback_message'] = (
            "I couldn't find the location from that. "
            "Please share either: 1) GPS coordinates (e.g., 13.0827, 80.2707), "
            "or 2) a specific address or landmark name."
        )
        
        return result


# Global location extractor instance
location_extractor = LocationExtractor()
