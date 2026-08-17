"""
Civic Complaint Intelligence Engine - Main FastAPI Application
Robust backend for handling citizen complaints with multi-modal data processing
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import custom modules
from config import settings
from audio_processor import audio_processor
from image_scrubber import image_scrubber
from location_extractor import location_extractor
from audio_transcriber import audio_transcriber

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('civic_complaint_engine.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Civic Complaint Intelligence Engine",
    description="Robust backend for processing multi-modal citizen complaints",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class ComplaintResponse(BaseModel):
    """Standardized response format for processed complaints"""
    success: bool
    complaint_id: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warnings: Optional[List[str]] = None
    requires_user_input: bool = False
    fallback_message: Optional[str] = None


class LocationUpdateRequest(BaseModel):
    """Request model for location update in fallback scenario"""
    complaint_id: str
    location_input: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    components: Dict[str, str]


# Storage for temporary complaint data (in production, use proper database)
complaint_storage = {}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify system status
    """
    # Determine which transcription service is configured
    transcription_provider = "none"
    if settings.sarvam_api_key:
        transcription_provider = "sarvam_ai"
    elif settings.openai_api_key:
        transcription_provider = "openai_whisper"
    elif audio_transcriber.whisper_model:
        transcription_provider = "local_whisper"
    
    components = {
        "audio_processor": "ready" if audio_processor else "not_initialized",
        "image_scrubber": "ready" if image_scrubber else "not_initialized",
        "location_extractor": "ready" if location_extractor else "not_initialized",
        "audio_transcriber": "ready" if audio_transcriber else "not_initialized",
        "transcription_provider": transcription_provider,
        "upload_directory": str(settings.upload_path)
    }
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        components=components
    )


@app.post("/api/complaint", response_model=ComplaintResponse)
async def submit_complaint(
    background_tasks: BackgroundTasks,
    text: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    gps_latitude: Optional[float] = Form(None),
    gps_longitude: Optional[float] = Form(None),
    language: Optional[str] = Form(None)
):
    """
    Main endpoint for submitting civic complaints
    Handles multi-modal input: text, audio, images, and GPS coordinates
    
    Implements the three required innovations:
    1. Edge-Processed Audio Compression
    2. Privacy-by-Design Image Scrubber  
    3. Interactive Missing-Data Fallback for location
    """
    complaint_id = str(uuid.uuid4())
    logger.info(f"Processing complaint {complaint_id}")
    
    try:
        # Initialize response data
        response_data = {
            "image_path": None,
            "transcribed_text": text or "",  # Use provided text if no audio
            "gps_coordinates": None,
            "audio_metadata": None,
            "image_metadata": None,
            "location_metadata": None,
            "transcription_metadata": None
        }
        
        warnings = []
        
        # Process audio file if provided
        transcribed_text = text or ""
        if audio:
            try:
                # Save uploaded audio file
                audio_filename = f"{complaint_id}_{audio.filename}"
                audio_path = settings.upload_path / audio_filename
                
                with open(audio_path, "wb") as audio_file:
                    content = await audio.read()
                    audio_file.write(content)
                
                logger.info(f"Audio file saved: {audio_path}")
                
                # Apply edge-processed audio compression
                processed_audio_path, audio_metadata = await audio_processor.process_audio_file(
                    str(audio_path)
                )
                response_data["audio_metadata"] = audio_metadata
                warnings.append(f"Audio compressed: {audio_metadata['compression_ratio']}x reduction")
                
                # Transcribe audio with error handling for noisy inputs
                transcription_result = await audio_transcriber.transcribe_audio(
                    processed_audio_path,
                    language=language
                )
                
                if transcription_result.get("error"):
                    warnings.append(f"Audio transcription issue: {transcription_result['error']}")
                    transcribed_text = transcription_result.get("text", "")
                else:
                    transcribed_text = transcription_result.get("text", "")
                    response_data["transcription_metadata"] = {
                        "language": transcription_result.get("language"),
                        "confidence": transcription_result.get("confidence"),
                        "method": transcription_result.get("method")
                    }
                
                response_data["transcribed_text"] = transcribed_text
                
            except Exception as e:
                error_msg = f"Audio processing failed: {str(e)}"
                logger.error(error_msg)
                warnings.append(error_msg)
        
        # Process image file if provided
        if image:
            try:
                # Save uploaded image file
                image_filename = f"{complaint_id}_{image.filename}"
                image_path = settings.upload_path / image_filename
                
                with open(image_path, "wb") as image_file:
                    content = await image.read()
                    image_file.write(content)
                
                logger.info(f"Image file saved: {image_path}")
                
                # Apply privacy-by-design image scrubbing
                scrubbed_image_path, image_metadata = await image_scrubber.scrub_image(
                    str(image_path)
                )
                response_data["image_path"] = scrubbed_image_path
                response_data["image_metadata"] = image_metadata
                
                if image_metadata.get("faces_detected", 0) > 0:
                    warnings.append(f"Privacy scrubbed: {image_metadata['faces_detected']} face(s) blurred")
                if image_metadata.get("license_plates_detected", 0) > 0:
                    warnings.append(f"Privacy scrubbed: {image_metadata['license_plates_detected']} license plate(s) blurred")
                
            except Exception as e:
                error_msg = f"Image processing failed: {str(e)}"
                logger.error(error_msg)
                warnings.append(error_msg)
        
        # Extract location with interactive fallback
        gps_coordinates = None
        if gps_latitude is not None and gps_longitude is not None:
            gps_coordinates = (gps_latitude, gps_longitude)
        
        location_result = await location_extractor.extract_location(
            text=transcribed_text,
            image_path=response_data.get("image_path"),
            gps_coordinates=gps_coordinates,
            enable_fallback=True
        )
        
        response_data["location_metadata"] = {
            "source": location_result.get("source"),
            "confidence": location_result.get("confidence"),
            "address": location_result.get("address")
        }
        
        if location_result.get("coordinates"):
            response_data["gps_coordinates"] = location_result["coordinates"]
        elif location_result.get("requires_user_input"):
            # Store complaint data for when user provides location
            complaint_storage[complaint_id] = {
                "data": response_data,
                "warnings": warnings,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return ComplaintResponse(
                success=False,
                complaint_id=complaint_id,
                timestamp=datetime.utcnow().isoformat(),
                error="Location required",
                warnings=warnings,
                requires_user_input=True,
                fallback_message=location_result.get("fallback_message")
            )
        
        # Store successful complaint
        complaint_storage[complaint_id] = {
            "data": response_data,
            "warnings": warnings,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return ComplaintResponse(
            success=True,
            complaint_id=complaint_id,
            timestamp=datetime.utcnow().isoformat(),
            data=response_data,
            warnings=warnings if warnings else None
        )
        
    except Exception as e:
        logger.error(f"Complaint processing failed: {e}")
        return ComplaintResponse(
            success=False,
            complaint_id=complaint_id,
            timestamp=datetime.utcnow().isoformat(),
            error=str(e)
        )


@app.post("/api/complaint/{complaint_id}/location", response_model=ComplaintResponse)
async def update_complaint_location(
    complaint_id: str,
    location_request: LocationUpdateRequest
):
    """
    Endpoint for users to provide missing location information
    Part of the interactive missing-data fallback system
    """
    logger.info(f"Updating location for complaint {complaint_id}")
    
    # Check if complaint exists and requires location
    if complaint_id not in complaint_storage:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    stored_complaint = complaint_storage[complaint_id]
    
    # Process user's location response
    location_result = await location_extractor.process_user_location_response(
        location_request.location_input
    )
    
    if location_result.get("coordinates"):
        # Update complaint with location
        stored_complaint["data"]["gps_coordinates"] = location_result["coordinates"]
        stored_complaint["data"]["location_metadata"] = {
            "source": location_result.get("source"),
            "confidence": location_result.get("confidence"),
            "address": location_result.get("address")
        }
        
        return ComplaintResponse(
            success=True,
            complaint_id=complaint_id,
            timestamp=datetime.utcnow().isoformat(),
            data=stored_complaint["data"],
            warnings=stored_complaint.get("warnings")
        )
    else:
        # Still need location
        return ComplaintResponse(
            success=False,
            complaint_id=complaint_id,
            timestamp=datetime.utcnow().isoformat(),
            error="Location still required",
            requires_user_input=True,
            fallback_message=location_result.get("fallback_message")
        )


@app.get("/api/complaint/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(complaint_id: str):
    """
    Retrieve complaint details by ID
    """
    if complaint_id not in complaint_storage:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    stored_complaint = complaint_storage[complaint_id]
    
    return ComplaintResponse(
        success=True,
        complaint_id=complaint_id,
        timestamp=stored_complaint["timestamp"],
        data=stored_complaint["data"],
        warnings=stored_complaint.get("warnings")
    )


@app.get("/api/complaints")
async def list_complaints():
    """
    List all complaints (for testing/debugging)
    """
    return {
        "total_complaints": len(complaint_storage),
        "complaints": [
            {
                "complaint_id": cid,
                "timestamp": data["timestamp"],
                "has_location": data["data"].get("gps_coordinates") is not None,
                "has_image": data["data"].get("image_path") is not None,
                "has_audio": data["data"].get("transcription_metadata") is not None
            }
            for cid, data in complaint_storage.items()
        ]
    }


def main():
    """
    Main entry point for running the server
    """
    logger.info("Starting Civic Complaint Intelligence Engine")
    
    # Ensure upload directory exists
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )


if __name__ == "__main__":
    main()
