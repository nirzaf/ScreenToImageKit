"""Service for managing temporary files."""

import os
import glob
import logging
from pathlib import Path
import time
import uuid
import tempfile

logger = logging.getLogger(__name__)

class TempFileService:
    """Service for managing temporary files in the application."""
    
    def __init__(self, temp_dir=None):
        """Initialize the temporary file service.
        
        Args:
            temp_dir (str, optional): Directory for temporary files. 
                                    If None, uses system temp directory.
        """
        if temp_dir:
            self.temp_dir = temp_dir
        else:
            # Create a subdirectory in the system temp directory
            self.temp_dir = os.path.join(tempfile.gettempdir(), "screentoimagekit")
            
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
        logger.debug(f"Using temporary directory: {self.temp_dir}")
        
    def cleanup_temp_files(self, pattern="s_*.png"):
        """Clean up temporary files matching the given pattern.
        
        Args:
            pattern (str): File pattern to match for cleanup
            
        Returns:
            bool: True if cleanup was successful, False otherwise
        """
        try:
            temp_path = Path(self.temp_dir)
            screenshot_files = list(temp_path.glob(pattern))
            
            for file_path in screenshot_files:
                try:
                    file_path.unlink()
                    logger.debug(f"Removed temporary file: {file_path}")
                except Exception as e:
                    logger.error(f"Error removing temporary file {file_path}: {e}")
                    
            return True
        except Exception as e:
            logger.error(f"Error during cleanup of temporary files: {e}")
            return False
            
    def cleanup_file(self, file_path):
        """Remove a specific temporary file.
        
        Args:
            file_path (str): Path to the file to remove
            
        Returns:
            bool: True if file was removed or doesn't exist, False on error
        """
        if not file_path:
            return True
            
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.debug(f"Removed temporary file: {path}")
            return True
        except Exception as e:
            logger.error(f"Error removing temporary file: {e}")
            return False
            
    def generate_temp_path(self, prefix="s", suffix=".png"):
        """Generate a path for a temporary file.
        
        Args:
            prefix (str): Prefix for the filename (default: 's' for screenshot)
            suffix (str): Suffix/extension for the filename
            
        Returns:
            str: Generated temporary file path
        """
        # Get current time in milliseconds (last 4 digits)
        timestamp = str(int(time.time() * 1000))[-4:]
        # Get first 4 chars of a UUID for uniqueness
        unique_id = str(uuid.uuid4())[:4]
        # Combine for a short, unique filename
        filename = f"{prefix}{timestamp}{unique_id}{suffix}"
        return str(Path(self.temp_dir) / filename)
