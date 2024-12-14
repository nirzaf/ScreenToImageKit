"""Image handling utilities for ScreenToImageKit."""

import os
import logging
from datetime import datetime
from PIL import ImageGrab, Image
import time

logger = logging.getLogger(__name__)

class ImageHandler:
    """Handles image capture and manipulation operations."""

    @staticmethod
    def capture_fullscreen(window_to_hide=None):
        """Capture full screen screenshot."""
        try:
            # Hide window if provided
            if window_to_hide:
                window_to_hide.withdraw()
                # Small delay to ensure window is hidden
                time.sleep(0.5)

            logger.debug("Capturing full screen")
            screenshot = ImageGrab.grab()
            
            # Generate temporary file path
            temp_path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
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

    @staticmethod
    def capture_area(coords):
        """Capture screenshot of specified area."""
        try:
            x1, y1, x2, y2 = map(int, coords)
            # Ensure coordinates are in correct order
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)

            logger.debug(f"Capturing area with coordinates: ({x1}, {y1}, {x2}, {y2})")
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            # Generate temporary file path
            temp_path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot.save(temp_path)
            logger.info(f"Screenshot saved temporarily as {temp_path}")
            
            return temp_path, screenshot
        except Exception as e:
            logger.error(f"Error capturing area: {e}")
            raise

    @staticmethod
    def resize_preview(image):
        """Resize image for preview."""
        try:
            return image.resize(
                (int(image.width / 2), int(image.height / 2)), 
                Image.LANCZOS
            )
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            raise

    @staticmethod
    def cleanup_temp_file(file_path):
        """Remove temporary screenshot file."""
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.debug(f"Temporary file {file_path} removed")
                return True
            except Exception as e:
                logger.error(f"Error removing temporary file: {e}")
                return False
        return True  # Return True if file doesn't exist

    @staticmethod
    def cleanup_all_temp_files():
        """Clean up all temporary screenshot files in the root directory."""
        try:
            import glob
            import os
            # Find all screenshot files in the root directory
            screenshot_files = glob.glob("screenshot_*.png")
            for file_path in screenshot_files:
                try:
                    os.remove(file_path)
                    logger.debug(f"Removed temporary file: {file_path}")
                except Exception as e:
                    logger.error(f"Error removing temporary file {file_path}: {e}")
            return True
        except Exception as e:
            logger.error(f"Error during cleanup of temporary files: {e}")
            return False
