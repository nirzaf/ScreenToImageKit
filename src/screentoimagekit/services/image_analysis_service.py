"""Service for analyzing images using Google's Gemini AI."""

import os
import logging
import google.generativeai as genai
from PIL import Image
import io
import time
import asyncio
import concurrent.futures
import threading
import base64

logger = logging.getLogger(__name__)

class ImageAnalysisService:
    """Service for analyzing images using Gemini AI."""
    
    def __init__(self):
        """Initialize the image analysis service."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.is_initialized = False
        self.timeout = 8  # Maximum wait time in seconds
        self.min_wait = 5  # Minimum wait time in seconds
        self._lock = threading.Lock()
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                
                # Configure Gemini Flash 2.0
                generation_config = {
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                }
                
                self.model = genai.GenerativeModel(
                    model_name="gemini-1.5-pro",  # Using the pro model for better image analysis
                    generation_config=generation_config
                )
                
                self.is_initialized = True
                logger.info("Gemini Pro Vision service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Pro Vision service: {str(e)}")
                if hasattr(e, 'status_code'):
                    logger.error(f"API Error Status Code: {e.status_code}")
                if hasattr(e, 'response'):
                    logger.error(f"API Error Response: {e.response}")

    def _encode_image(self, image_path):
        """Convert image to base64 encoding.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: Image data in Gemini-compatible format
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

    async def _analyze_with_timeout(self, image_data, prompt):
        """Analyze image with timeout using asyncio."""
        try:
            # Create an executor for running the blocking API call
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Start time for tracking
                start_time = time.time()
                
                # Run the API call in the executor (thread-safe)
                with self._lock:
                    future = executor.submit(
                        self.model.generate_content,
                        [image_data, prompt]
                    )
                
                # Wait for minimum time
                await asyncio.sleep(self.min_wait)
                
                # Calculate remaining time
                elapsed = time.time() - start_time
                remaining = max(0, self.timeout - elapsed)
                
                try:
                    # Wait for completion or timeout
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
            logger.error(f"Error in _analyze_with_timeout: {str(e)}")
            return None
    
    async def analyze_image_async(self, image_path, max_words=5):
        """Analyze image asynchronously and return a concise description.
        
        Args:
            image_path (str): Path to the image file
            max_words (int): Maximum number of words in description
            
        Returns:
            str: Concise description of the image content
        """
        if not self.is_initialized:
            logger.error("Gemini Pro Vision service not initialized - missing or invalid API key")
            return None
            
        try:
            logger.info(f"Starting async image analysis for: {image_path}")
            
            # Encode image to base64
            image_data = self._encode_image(image_path)
            if not image_data:
                logger.error("Failed to encode image")
                return None
            
            # Create prompt for concise description
            prompt = f"Describe what's in this image in {max_words} words or less. Focus on the main subject or action. Use lowercase words separated by underscores. Do not use any special characters or spaces."
            
            logger.debug(f"Sending request to Gemini Pro Vision with prompt: {prompt}")
            
            # Run analysis with timeout
            response = await self._analyze_with_timeout(image_data, prompt)
            
            if response and response.text:
                raw_description = response.text.strip()
                logger.info(f"Raw Gemini Pro Vision response: {raw_description}")
                
                # Clean up the description
                description = raw_description.lower()
                # Remove any special characters and spaces
                description = "".join(c for c in description if c.isalnum() or c == '_')
                # Ensure it's not too long
                words = description.split('_')
                if len(words) > max_words:
                    words = words[:max_words]
                description = '_'.join(words)
                
                logger.info(f"Final processed description: {description}")
                return description
            else:
                if hasattr(response, 'prompt_feedback'):
                    logger.error(f"Gemini Pro Vision safety issues: {response.prompt_feedback}")
                else:
                    logger.error("Gemini Pro Vision returned empty response or timed out")
                return None
            
        except Exception as e:
            logger.error(f"Error during image analysis: {str(e)}")
            if hasattr(e, 'status_code'):
                logger.error(f"API Error Status Code: {e.status_code}")
            if hasattr(e, 'response'):
                logger.error(f"API Error Response: {e.response}")
            return None

    def analyze_image(self, image_path, max_words=5):
        """Analyze image and return a concise description.
        
        Args:
            image_path (str): Path to the image file
            max_words (int): Maximum number of words in description
            
        Returns:
            str: Concise description of the image content
        """
        if not self.is_initialized:
            logger.error("Gemini Pro Vision service not initialized - missing or invalid API key")
            return None
            
        try:
            logger.info(f"Starting image analysis for: {image_path}")
            
            # Encode image to base64
            image_data = self._encode_image(image_path)
            if not image_data:
                logger.error("Failed to encode image")
                return None
            
            # Create prompt for concise description
            prompt = f"Describe what's in this image in {max_words} words or less. Focus on the main subject or action. Use lowercase words separated by underscores. Do not use any special characters or spaces."
            
            logger.debug(f"Sending request to Gemini Pro Vision with prompt: {prompt}")
            
            # Run analysis with timeout using asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(self._analyze_with_timeout(image_data, prompt))
            finally:
                loop.close()
            
            if response and response.text:
                raw_description = response.text.strip()
                logger.info(f"Raw Gemini Pro Vision response: {raw_description}")
                
                # Clean up the description
                description = raw_description.lower()
                # Remove any special characters and spaces
                description = "".join(c for c in description if c.isalnum() or c == '_')
                # Ensure it's not too long
                words = description.split('_')
                if len(words) > max_words:
                    words = words[:max_words]
                description = '_'.join(words)
                
                logger.info(f"Final processed description: {description}")
                return description
            else:
                if hasattr(response, 'prompt_feedback'):
                    logger.error(f"Gemini Pro Vision safety issues: {response.prompt_feedback}")
                else:
                    logger.error("Gemini Pro Vision returned empty response or timed out")
                return None
            
        except Exception as e:
            logger.error(f"Error during image analysis: {str(e)}")
            if hasattr(e, 'status_code'):
                logger.error(f"API Error Status Code: {e.status_code}")
            if hasattr(e, 'response'):
                logger.error(f"API Error Response: {e.response}")
            return None
