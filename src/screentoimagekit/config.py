"""Configuration management for ScreenToImageKit."""

import os
import logging
from cryptography.fernet import Fernet
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Constants
CREDENTIALS_FILE = "imagekit_credentials.dat"
KEY_FILE = "encryption_key.key"
ENV_FILE = ".env"

class CredentialsError(Exception):
    """Exception raised for credential-related errors."""
    pass

def encrypt_credentials(private_key, public_key, url_endpoint, key):
    """Encrypts ImageKit credentials using Fernet."""
    f = Fernet(key)
    credentials = f"{private_key}:{public_key}:{url_endpoint}"
    encrypted_credentials = f.encrypt(credentials.encode())
    return encrypted_credentials

def decrypt_credentials(encrypted_credentials, key):
    """Decrypts ImageKit credentials using Fernet."""
    try:
        f = Fernet(key)
        decrypted_credentials = f.decrypt(encrypted_credentials).decode()
        creds = decrypted_credentials.split(':')
        if len(creds) != 3:
            raise CredentialsError("Invalid credential format")
        return creds[0], creds[1], creds[2]
    except Exception as e:
        logger.error(f"Error decrypting credentials: {e}")
        raise CredentialsError(f"Error decrypting credentials: {e}") from e

class ConfigManager:
    """Manages application configuration and credentials."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self.env_loaded = False
        self.load_env()
    
    def load_env(self):
        """Load environment variables from .env file."""
        try:
            # Load from .env file
            if os.path.exists(ENV_FILE):
                load_dotenv(ENV_FILE)
                self.env_loaded = True
                logger.info(".env file loaded successfully")
            else:
                logger.warning(".env file not found")
        except Exception as e:
            logger.error(f"Error loading .env file: {e}")
            self.env_loaded = False
    
    def get(self, key, default=None):
        """Get a configuration value.
        
        Args:
            key: Configuration key to get
            default: Default value if key not found
            
        Returns:
            str: Configuration value or default
        """
        try:
            value = os.getenv(key, default)
            if value is None:
                logger.warning(f"Configuration key '{key}' not found")
            return value
        except Exception as e:
            logger.error(f"Error getting configuration value for '{key}': {e}")
            return default
    
    @staticmethod
    def load_env_credentials():
        """Load credentials from .env file."""
        try:
            # Try to load from .env file
            if os.path.exists(ENV_FILE):
                load_dotenv(ENV_FILE)
                private_key = os.getenv('PRIVATE_KEY')
                public_key = os.getenv('PUBLIC_KEY')
                url_endpoint = os.getenv('URL_ENDPOINT')
                
                # Check if all required credentials are present
                if not all([private_key, public_key, url_endpoint]):
                    logger.warning("Some credentials missing from .env file")
                    return None, None, None
                    
                logger.info("Credentials loaded from .env file")
                return private_key, public_key, url_endpoint
                
            logger.warning(".env file not found")
            return None, None, None
            
        except Exception as e:
            logger.error(f"Error loading credentials from .env: {e}")
            return None, None, None
    
    def save_credentials(self, private_key, public_key, url_endpoint):
        """Save ImageKit credentials to encrypted file."""
        try:
            # Generate encryption key if it doesn't exist
            if not os.path.exists(KEY_FILE):
                key = Fernet.generate_key()
                with open(KEY_FILE, 'wb') as f:
                    f.write(key)
            else:
                with open(KEY_FILE, 'rb') as f:
                    key = f.read()
            
            # Encrypt and save credentials
            encrypted_credentials = encrypt_credentials(private_key, public_key, url_endpoint, key)
            with open(CREDENTIALS_FILE, 'wb') as f:
                f.write(encrypted_credentials)
                
            logger.info("Credentials saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            return False
    
    def load_credentials(self):
        """Load ImageKit credentials from encrypted file."""
        try:
            # Check if files exist
            if not os.path.exists(CREDENTIALS_FILE) or not os.path.exists(KEY_FILE):
                logger.warning("Credentials or key file not found")
                return None, None, None
            
            # Load key and encrypted credentials
            with open(KEY_FILE, 'rb') as f:
                key = f.read()
            with open(CREDENTIALS_FILE, 'rb') as f:
                encrypted_credentials = f.read()
            
            # Decrypt credentials
            private_key, public_key, url_endpoint = decrypt_credentials(encrypted_credentials, key)
            logger.info("Credentials loaded successfully")
            return private_key, public_key, url_endpoint
            
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return None, None, None
