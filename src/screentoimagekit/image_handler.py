"""Image handling and processing for ScreenToImageKit."""

import os
import tempfile
import logging
from PIL import Image, ImageGrab
from datetime import datetime
import google.generativeai as genai
from pathlib import Path

logger = logging.getLogger(__name__)

class ImageHandler:
    """Handles image capture, processing, and analysis."""

    def __init__(self, gemini_api_key=None):
        """Initialize the image handler.
        
        Args:
            gemini_api_key: API key for Google's Gemini API
        """
        self.temp_dir = os.path.join(tempfile.gettempdir(), "screentoimagekit")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Initialize Gemini if API key is provided
        self.gemini_model = None
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro-vision')

    def capture_area(self, coords):
        """Capture a specific area of the screen.
        
        Args:
            coords: Tuple of (x1, y1, x2, y2) coordinates
        
        Returns:
            Tuple of (temp_path, PIL.Image)
        """
        try:
            # Ensure coordinates are integers
            x1, y1, x2, y2 = map(int, coords)
            bbox = (x1, y1, x2, y2)
            
            # Capture the screenshot
            screenshot = ImageGrab.grab(bbox=bbox)
            
            # Save to temp file
            temp_path = os.path.join(self.temp_dir, f"s{datetime.now().strftime('%H%M%S%f')}.png")
            screenshot.save(temp_path)
            
            logger.info(f"Screenshot captured and saved to {temp_path}")
            return temp_path, screenshot
            
        except Exception as e:
            logger.error(f"Error capturing area: {e}")
            return None, None

    def capture_fullscreen(self):
        """Capture the entire screen.
        
        Returns:
            Tuple of (temp_path, PIL.Image)
        """
        try:
            # Capture full screen
            screenshot = ImageGrab.grab()
            
            # Save to temp file
            temp_path = os.path.join(self.temp_dir, f"s{datetime.now().strftime('%H%M%S%f')}.png")
            screenshot.save(temp_path)
            
            logger.info(f"Full screen captured and saved to {temp_path}")
            return temp_path, screenshot
            
        except Exception as e:
            logger.error(f"Error capturing full screen: {e}")
            return None, None

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

            # Load the image
            image = Image.open(image_path)
            
            # Generate description
            response = self.gemini_model.generate_content(["Describe this screenshot in a few words", image])
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
            
            # Create new filename
            dir_path = os.path.dirname(temp_path)
            ext = Path(temp_path).suffix
            new_path = os.path.join(dir_path, f"{clean_desc}{ext}")
            
            # Rename file
            os.rename(temp_path, new_path)
            logger.info(f"Renamed {temp_path} to {new_path}")
            
            return new_path
            
        except Exception as e:
            logger.error(f"Error renaming file: {e}")
            return temp_path
