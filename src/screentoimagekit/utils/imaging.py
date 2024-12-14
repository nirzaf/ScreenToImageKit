"""Image handling utilities for ScreenToImageKit."""

import logging
from datetime import datetime
from PIL import ImageGrab, Image
import time

logger = logging.getLogger(__name__)

class ImageHandler:
    """Handles image capture and processing operations."""
    
    def __init__(self, temp_file_service):
        """Initialize ImageHandler with dependencies.
        
        Args:
            temp_file_service: Service for managing temporary files
        """
        self.temp_file_service = temp_file_service
    
    def capture_fullscreen(self, window_to_hide=None):
        """Capture full screen screenshot.
        
        Args:
            window_to_hide: Optional window to hide during capture
            
        Returns:
            tuple: (temp_path, screenshot) Temporary file path and PIL Image
        """
        try:
            # Hide window if provided
            if window_to_hide:
                window_to_hide.withdraw()
                # Small delay to ensure window is hidden
                time.sleep(0.5)

            logger.debug("Capturing full screen")
            screenshot = ImageGrab.grab()
            
            # Generate and save to temporary file
            temp_path = self.temp_file_service.generate_temp_path()
            screenshot.save(temp_path)
            logger.info(f"Screenshot saved temporarily as {temp_path}")
            
            # Show window again if it was hidden
            if window_to_hide:
                window_to_hide.deiconify()
            
            return temp_path, screenshot
        except Exception as e:
            logger.error(f"Error capturing full screen: {e}")
            if window_to_hide:
                window_to_hide.deiconify()
            raise
    
    def capture_area(self, coords):
        """Capture screenshot of specified area.
        
        Args:
            coords: Tuple of coordinates (x1, y1, x2, y2)
            
        Returns:
            tuple: (temp_path, screenshot) Temporary file path and PIL Image
        """
        try:
            x1, y1, x2, y2 = map(int, coords)
            # Ensure coordinates are in correct order
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)

            logger.debug(f"Capturing area with coordinates: ({x1}, {y1}, {x2}, {y2})")
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            # Generate and save to temporary file
            temp_path = self.temp_file_service.generate_temp_path()
            screenshot.save(temp_path)
            logger.info(f"Screenshot saved temporarily as {temp_path}")
            
            return temp_path, screenshot
        except Exception as e:
            logger.error(f"Error capturing area: {e}")
            raise
    
    @staticmethod
    def resize_preview(image):
        """Resize image for preview.
        
        Args:
            image: PIL Image to resize
            
        Returns:
            PIL.Image: Resized image
        """
        try:
            return image.resize(
                (int(image.width / 2), int(image.height / 2)), 
                Image.LANCZOS
            )
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            raise
    
    def cleanup_temp_file(self, file_path):
        """Remove temporary screenshot file.
        
        Args:
            file_path: Path to the file to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.temp_file_service.cleanup_file(file_path)
    
    def cleanup_all_temp_files(self):
        """Clean up all temporary screenshot files.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.temp_file_service.cleanup_temp_files()
