"""ImageKit service integration for ScreenToImageKit."""

import logging
import pyperclip
import os
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

    def upload_file(self, file_path):
        """Upload file to ImageKit."""
        if not self.imagekit:
            raise ValueError("ImageKit not initialized")

        try:
            options = UploadFileRequestOptions(
                response_fields=["is_private_file", "tags"],
                tags=["screenshot"],
                folder="/screenshots"
            )

            with open(file_path, 'rb') as file:
                # Use the basename of the file as the ImageKit filename
                file_name = os.path.basename(file_path)
                upload = self.imagekit.upload_file(
                    file=file,
                    file_name=file_name,
                    options=options
                )

                if upload and hasattr(upload, 'url'):
                    # Copy URL to clipboard
                    pyperclip.copy(upload.url)
                    logger.info(f"File uploaded successfully: {upload.url}")
                    return upload.url
                else:
                    raise Exception("Upload failed: Invalid response from ImageKit")

        except Exception as e:
            logger.error(f"Error uploading to ImageKit: {e}")
            raise

    @property
    def is_configured(self):
        """Check if ImageKit is properly configured."""
        return self.imagekit is not None
