"""ImageKit service integration for ScreenToImageKit."""

import logging
import pyperclip
import os
import time
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions

logger = logging.getLogger(__name__)

class ImageKitService:
    """Handles ImageKit integration and file uploads."""

    def __init__(self, private_key=None, public_key=None, url_endpoint=None):
        """Initialize ImageKit service with credentials."""
        self.imagekit = None
        if all([private_key, public_key, url_endpoint]):
            self.initialize(private_key, public_key, url_endpoint)

    def initialize(self, private_key, public_key, url_endpoint):
        """Initialize or reinitialize ImageKit client."""
        try:
            self.imagekit = ImageKit(
                private_key=private_key,
                public_key=public_key,
                url_endpoint=url_endpoint
            )
            return True
        except Exception as e:
            logger.error(f"Error initializing ImageKit: {e}")
            self.imagekit = None
            return False

    def upload_file(self, file_path, max_retries=3, retry_delay=1):
        """Upload file to ImageKit with retries.
        
        Args:
            file_path: Path to the file to upload
            max_retries: Maximum number of upload attempts
            retry_delay: Delay between retries in seconds
        """
        if not self.imagekit:
            error_msg = "ImageKit not initialized - check your API credentials"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        last_error = None
        for attempt in range(max_retries):
            try:
                logger.debug(f"Upload attempt {attempt + 1}/{max_retries} for file: {file_path}")
                
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File disappeared during upload attempt: {file_path}")

                options = UploadFileRequestOptions(
                    response_fields=["is_private_file", "tags"],
                    tags=["screenshot"],
                    folder="/screenshots"
                )

                with open(file_path, 'rb') as file:
                    file_name = os.path.basename(file_path)
                    logger.debug(f"Uploading file with name: {file_name}")
                    
                    try:
                        upload = self.imagekit.upload_file(
                            file=file,
                            file_name=file_name,
                            options=options
                        )
                        
                        if upload and hasattr(upload, 'url'):
                            logger.info(f"Upload successful on attempt {attempt + 1}. URL: {upload.url}")
                            pyperclip.copy(upload.url)
                            return upload.url
                        else:
                            raise Exception(f"Invalid response from ImageKit: {upload}")
                            
                    except Exception as e:
                        logger.error(f"ImageKit API error on attempt {attempt + 1}: {str(e)}")
                        if hasattr(e, '__traceback__'):
                            import traceback
                            logger.error(f"Stack trace:\n{''.join(traceback.format_tb(e.__traceback__))}")
                        last_error = e
                        raise

            except Exception as e:
                last_error = e
                error_msg = f"Upload attempt {attempt + 1} failed: {str(e)}"
                if hasattr(e, '__traceback__'):
                    import traceback
                    error_msg += f"\nStack trace:\n{''.join(traceback.format_tb(e.__traceback__))}"
                logger.error(error_msg)
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                continue

        # If we get here, all retries failed
        final_error = f"All {max_retries} upload attempts failed."
        if last_error:
            final_error += f" Last error: {str(last_error)}"
        logger.error(final_error)
        raise Exception(final_error)

    @property
    def is_configured(self):
        """Check if ImageKit is properly configured."""
        return self.imagekit is not None
