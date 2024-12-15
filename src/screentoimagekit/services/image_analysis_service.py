"""Service for analyzing images using Google's Gemini AI."""

import os
import logging
import google.generativeai as genai
import asyncio
import concurrent.futures
import threading
import base64
from typing import Optional, Dict, Any
import time
import re
from datetime import datetime

logger = logging.getLogger(__name__)

def _encode_image(image_path: str) -> Optional[Dict[str, str]]:
    """Convert image to base64 encoding.

    Args:
        image_path (str): Path to the image file

    Returns:
        Optional[Dict[str, str]]: Image data in Gemini-compatible format or None if error
    """
    try:
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            return {
                'mime_type': 'image/jpeg',
                'data': base64_data
            }
    except Exception as e:
        logger.error(f"Error encoding image: {str(e)}")
        return None

class ImageAnalysisService:
    """Service for analyzing images using Gemini AI."""

    def __init__(self):
        """Initialize the image analysis service."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.is_initialized = False
        self.timeout = 10  # Maximum wait time in seconds
        self.min_wait = 1  # Minimum wait time in seconds
        self._lock = threading.Lock()

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)

                generation_config = {
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                }

                self.model = genai.GenerativeModel(
                    model_name="gemini-1.5-pro",
                    generation_config=generation_config
                )

                self.is_initialized = True
                logger.info("Gemini Pro Vision service initialized successfully")
            except Exception as e:
                self._log_error("Failed to initialize Gemini Pro Vision service", e)

    def _log_error(self, message: str, error: Exception) -> None:
        """Centralized error logging."""
        logger.error(f"{message}: {str(error)}")
        if hasattr(error, 'status_code'):
            logger.error(f"API Error Status Code: {error.status_code}")
        if hasattr(error, 'response'):
            logger.error(f"API Error Response: {error.response}")

    def _format_description(self, description):
        """Format the description for use in filename.
        
        Args:
            description: Raw description from Gemini AI
            
        Returns:
            Formatted description that fits naming requirements:
            - Between 30-40 characters
            - Format: description_HHMM
            - Only valid filename characters
        """
        try:
            # Clean the description: lowercase and replace invalid chars
            clean_desc = re.sub(r'[^a-zA-Z0-9_]', '_', description.lower())
            
            # Remove consecutive underscores
            clean_desc = re.sub(r'_+', '_', clean_desc)
            
            # Get current time in HHMM format
            current_time = datetime.now().strftime("%H%M")
            
            # Target length for description (excluding _HHMM suffix)
            # We need room for _HHMM (5 chars) in the final 30-40 char range
            target_min = 25  # 30 - 5
            target_max = 35  # 40 - 5
            
            # Adjust description length
            if len(clean_desc) < target_min:
                # Pad with meaningful words if too short
                padding_words = ["screenshot", "image", "capture"]
                while len(clean_desc) < target_min and padding_words:
                    clean_desc = f"{clean_desc}_{padding_words.pop(0)}"
            elif len(clean_desc) > target_max:
                # Truncate if too long, but keep whole words
                clean_desc = clean_desc[:target_max]
                last_underscore = clean_desc.rfind('_')
                if last_underscore > target_min:
                    clean_desc = clean_desc[:last_underscore]
            
            # Final filename: description_HHMM
            final_name = f"{clean_desc}_{current_time}"
            
            # Validate final length
            if not (30 <= len(final_name) <= 40):
                logger.warning(f"Generated filename length ({len(final_name)}) outside target range: {final_name}")
                
            logger.debug(f"Formatted description: {final_name} (length: {len(final_name)})")
            return final_name
            
        except Exception as e:
            logger.error(f"Error formatting description: {e}")
            # Return a safe default name that meets length requirements
            timestamp = datetime.now().strftime("%H%M")
            return f"screenshot_capture_image_{timestamp}"

    def _process_description(self, raw_description: str, max_words: int) -> str:
        """Process and clean the raw description from Gemini.

        Args:
            raw_description (str): Raw description from Gemini
            max_words (int): Maximum number of words allowed

        Returns:
            str: Processed description
        """
        # Clean up the description
        description = raw_description.lower()
        # Remove any special characters and spaces
        description = "".join(c for c in description if c.isalnum() or c == '_')
        # Ensure it's not too long
        words = description.split('_')
        if len(words) > max_words:
            words = words[:max_words]
        return '_'.join(words)

    async def _analyze_with_timeout(self, image_data: Dict[str, str], prompt: str) -> Optional[Any]:
        """Analyze image with timeout using asyncio."""
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                start_time = time.time()

                with self._lock:
                    future = executor.submit(
                        self.model.generate_content,
                        [image_data, prompt]
                    )

                await asyncio.sleep(self.min_wait)

                elapsed = time.time() - start_time
                remaining = max(0, self.timeout - elapsed)

                try:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: future.result(timeout=remaining)
                    )
                    logger.info(f"Gemini API response received in {elapsed:.2f} seconds")
                    return response
                except concurrent.futures.TimeoutError:
                    logger.warning(f"Gemini API timeout after {self.timeout} seconds")
                    return None

        except Exception as e:
            self._log_error("Error in _analyze_with_timeout", e)
            return None

    async def _analyze_image_internal(self, image_path: str, max_words: int = 5) -> Optional[str]:
        """Internal method for image analysis shared by both sync and async interfaces."""
        if not self.is_initialized:
            logger.error("Gemini Pro Vision service not initialized - missing or invalid API key")
            return None

        try:
            logger.info(f"Starting image analysis for: {image_path}")

            image_data = _encode_image(image_path)
            if not image_data:
                logger.error("Failed to encode image")
                return None

            prompt = f"Describe what's in this image in {max_words} words or less. Focus on the main subject or action. Use lowercase words separated by underscores. Do not use any special characters or spaces."

            logger.debug(f"Sending request to Gemini Pro Vision with prompt: {prompt}")

            response = await self._analyze_with_timeout(image_data, prompt)

            if response and response.text:
                raw_description = response.text.strip()
                logger.info(f"Raw Gemini Pro Vision response: {raw_description}")
                return self._process_description(raw_description, max_words)
            else:
                if hasattr(response, 'prompt_feedback'):
                    logger.error(f"Gemini Pro Vision safety issues: {response.prompt_feedback}")
                else:
                    logger.error("Gemini Pro Vision returned empty response or timed out")
                return None

        except Exception as e:
            self._log_error("Error during image analysis", e)
            return None

    async def analyze_image_async(self, image_path: str, use_gemini: bool = True) -> Optional[str]:
        """Analyze image asynchronously with timeout.

        Args:
            image_path: Path to the image file
            use_gemini: Whether to use Gemini AI for analysis

        Returns:
            Optional[str]: Image description or None if analysis fails/times out
        """
        if not use_gemini or not self.is_initialized:
            logger.info("Skipping Gemini analysis (disabled or not initialized)")
            return None

        try:
            with open(image_path, 'rb') as image_file:
                image_data = {
                    'mime_type': 'image/png',
                    'data': base64.b64encode(image_file.read()).decode('utf-8')
                }

            prompt = """
            Analyze this screenshot and provide a very concise name (3-4 words maximum) that describes its content.
            Use only lowercase letters, numbers, and underscores.
            Focus on the main subject or action in the image.
            Example responses:
            - login_page_dark
            - dashboard_stats_view
            - code_editor_python
            - error_message_dialog
            """
            
            response = await self._analyze_with_timeout(image_data, prompt)
            
            if response and response.text:
                # Format the description
                formatted_desc = self._format_description(response.text.strip())
                logger.info(f"Gemini generated description: {formatted_desc}")
                return formatted_desc
            
            logger.warning("No valid response from Gemini")
            return None

        except Exception as e:
            self._log_error("Error in analyze_image_async", e)
            return None

    def analyze_image(self, image_path: str, max_words: int = 5) -> Optional[str]:
        """Analyze image synchronously and return a concise description."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._analyze_image_internal(image_path, max_words))
        finally:
            loop.close()