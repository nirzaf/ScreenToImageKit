"""Image handling service for capturing and processing screenshots."""

import os
import logging
from PIL import Image, ImageGrab
from datetime import datetime
import google.generativeai as genai
from pathlib import Path
from .temp_file_service import TempFileService

logger = logging.getLogger(__name__)

class ImageHandler:
    """Handles image capture and processing operations."""
    
    def __init__(self, temp_file_service: TempFileService = None, gemini_api_key: str = None):
        """Initialize the image handler.
        
        Args:
            temp_file_service: Service for managing temporary files
            gemini_api_key: API key for Google's Gemini API
        """
        self.temp_file_service = temp_file_service or TempFileService()
        
        # Initialize Gemini if API key is provided
        self.gemini_model = None
        if gemini_api_key:
            try:
                genai.configure(api_key=gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-pro-vision')
                logger.info("Gemini model initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini model: {e}")

    def capture_area(self, coords):
        """Capture a screenshot of the specified area.
        
        Args:
            coords: A tuple of (left, top, right, bottom) coordinates
            
        Returns:
            tuple: (temp_file_path, screenshot_image)
        """
        try:
            # Ensure coordinates are integers
            coords = tuple(int(x) for x in coords)
            logger.debug(f"Capturing area with coordinates: {coords}")
            
            # Capture the screenshot
            screenshot = ImageGrab.grab(bbox=coords)
            
            # Save to temporary file
            temp_path = self.temp_file_service.generate_temp_path()
            screenshot.save(temp_path, format="PNG")
            
            logger.info(f"Screenshot captured and saved to {temp_path}")
            return temp_path, screenshot
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            raise

    def capture_fullscreen(self):
        """Capture a full screen screenshot.
        
        Returns:
            tuple: (temp_file_path, screenshot_image)
        """
        try:
            # Capture the screenshot
            screenshot = ImageGrab.grab()
            
            # Save to temporary file
            temp_path = self.temp_file_service.generate_temp_path()
            screenshot.save(temp_path, format="PNG")
            
            logger.info(f"Full screen captured and saved to {temp_path}")
            return temp_path, screenshot
            
        except Exception as e:
            logger.error(f"Error capturing full screen: {e}")
            raise

    def get_image_description(self, image_path):
        """Get a description of the image using Gemini Vision.
        
        Args:
            image_path: Path to the image file
        
        Returns:
            str: Description of the image, or None if failed
        """
        try:
            if not self.gemini_model:
                logger.warning("Gemini model not initialized - no API key provided")
                return None

            # Load and prepare the image
            with Image.open(image_path) as image:
                # Convert to RGB if needed
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Generate description
                response = self.gemini_model.generate_content(
                    ["Describe this screenshot in a few words that would make a good filename", image],
                    generation_config={
                        'temperature': 0.1,  # More focused output
                        'max_output_tokens': 50  # Short description
                    }
                )
                
                if not response.text:
                    logger.warning("Gemini returned empty response")
                    return None
                    
                description = response.text.strip()
                logger.info(f"Generated description: {description}")
                return description
            
        except Exception as e:
            logger.error(f"Error getting image description: {e}")
            return None

    def rename_with_description(self, temp_path, description):
        """Rename the image file using the description.
        
        Args:
            temp_path: Current path to the image
            description: Description to use in filename
        
        Returns:
            str: New path to the image
        """
        try:
            if not description:
                return temp_path
                
            # Clean up description for filename
            clean_desc = "".join(c if c.isalnum() or c in " -_" else "_" for c in description)
            clean_desc = clean_desc.strip().replace(" ", "_")[:50]  # Limit length
            
            # Create new filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dir_path = os.path.dirname(temp_path)
            ext = Path(temp_path).suffix
            new_path = os.path.join(dir_path, f"{clean_desc}_{timestamp}{ext}")
            
            # Rename file
            os.rename(temp_path, new_path)
            logger.info(f"Renamed {temp_path} to {new_path}")
            
            return new_path
            
        except Exception as e:
            logger.error(f"Error renaming file: {e}")
            return temp_path

    def resize_preview(self, image, max_size=(800, 600)):
        """Resize an image for preview while maintaining aspect ratio.
        
        Args:
            image: PIL Image object
            max_size: Maximum dimensions (width, height)
            
        Returns:
            PIL Image: Resized image
        """
        try:
            # Calculate aspect ratio
            ratio = min(max_size[0] / image.width, max_size[1] / image.height)
            
            # Only resize if image is larger than max_size
            if ratio < 1:
                new_size = (int(image.width * ratio), int(image.height * ratio))
                return image.resize(new_size, Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            raise

    def cleanup_temp_file(self, temp_path):
        """Clean up a temporary file.
        
        Args:
            temp_path: Path to the temporary file
        """
        try:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
                logger.debug(f"Cleaned up temporary file: {temp_path}")
        except Exception as e:
            logger.error(f"Error cleaning up temporary file: {e}")
