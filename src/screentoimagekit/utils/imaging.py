"""Image handling utilities for ScreenToImageKit."""

import logging
from datetime import datetime
from PIL import ImageGrab, Image
import time
import os
from ..services.image_analysis_service import ImageAnalysisService
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class ImageHandler:
    """Handles image capture and processing operations."""
    
    def __init__(self, temp_file_service=None):
        """Initialize ImageHandler with dependencies.
        
        Args:
            temp_file_service: Service for managing temporary files
        """
        self.temp_file_service = temp_file_service or TempFileService()
        self.image_analysis = ImageAnalysisService()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._processing_lock = threading.Lock()
    
    def _process_image_async(self, temp_path, callback=None):
        """Process image analysis and renaming in background thread."""
        def _background_task():
            try:
                if not self.image_analysis.is_initialized:
                    logger.info("Using default naming strategy (Gemini AI not initialized)")
                    if callback:
                        callback(temp_path)
                    return
                
                logger.info("Starting Gemini AI analysis in background...")
                
                # Create event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Run analysis
                    description = loop.run_until_complete(
                        self.image_analysis.analyze_image_async(temp_path)
                    )
                    
                    if description:
                        # Create new path with description
                        directory = os.path.dirname(temp_path)
                        filename = f"{description}.png"
                        new_path = os.path.join(directory, filename)
                        
                        # Rename the file
                        with self._processing_lock:
                            if os.path.exists(temp_path):  # Check if original file still exists
                                os.rename(temp_path, new_path)
                                logger.info(f"File renamed with AI description: {new_path}")
                                if callback:
                                    callback(new_path)
                                return
                    
                    logger.info("Using default naming strategy (Gemini AI analysis failed or timed out)")
                    if callback:
                        callback(temp_path)
                        
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.error(f"Error in background processing: {e}")
                if callback:
                    callback(temp_path)
        
        # Submit background task
        self.executor.submit(_background_task)
    
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
    
    def capture_area(self, area, callback=None):
        """Capture screenshot of specified area.
        
        Args:
            area (tuple): Area coordinates (x1, y1, x2, y2)
            callback (callable): Optional callback function to receive the final file path
            
        Returns:
            tuple: (temp_file_path, image_data) if successful, (None, None) if failed
        """
        try:
            x1, y1, x2, y2 = area
            
            # Ensure coordinates form a valid rectangle
            if x1 == x2 or y1 == y2:
                logger.error("Invalid selection area: Selection must have both width and height")
                return None, None
                
            # Ensure x1 < x2 and y1 < y2
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            
            # Ensure minimum size (at least 10x10 pixels)
            if (x2 - x1) < 10 or (y2 - y1) < 10:
                logger.error("Selection area too small: Must be at least 10x10 pixels")
                return None, None
            
            logger.debug(f"Capturing area with coordinates: ({x1}, {y1}, {x2}, {y2})")
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            # Generate temp file path with timestamp for uniqueness
            temp_path = self.temp_file_service.generate_temp_path()
            
            # Save screenshot with temporary name
            screenshot.save(temp_path)
            logger.debug(f"Screenshot saved to temporary path: {temp_path}")
            
            # Start async processing
            self._process_image_async(temp_path, callback)
            
            return temp_path, screenshot
            
        except Exception as e:
            logger.error(f"Error capturing area: {e}")
            return None, None
    
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
