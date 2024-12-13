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
                
                if all([private_key, public_key, url_endpoint]):
                    logger.info("Credentials loaded from .env file")
                    return private_key, public_key, url_endpoint
            return None, None, None
        except Exception as e:
            logger.error(f"Error loading .env credentials: {e}")
            return None, None, None
    
    @staticmethod
    def save_credentials(private_key, public_key, url_endpoint):
        """Save ImageKit credentials securely."""
        try:
            if not os.path.exists(KEY_FILE):
                key = Fernet.generate_key()
                with open(KEY_FILE, "wb") as key_file:
                    key_file.write(key)
            else:
                with open(KEY_FILE, "rb") as key_file:
                    key = key_file.read()

            encrypted_credentials = encrypt_credentials(
                private_key, public_key, url_endpoint, key
            )
            with open(CREDENTIALS_FILE, "wb") as cred_file:
                cred_file.write(encrypted_credentials)
            return True
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            return False

    @staticmethod
    def load_credentials():
        """Load ImageKit credentials from encrypted file or .env."""
        try:
            # First try to load from .env file
            private_key, public_key, url_endpoint = ConfigManager.load_env_credentials()
            if all([private_key, public_key, url_endpoint]):
                return private_key, public_key, url_endpoint

            # If .env credentials not found, try encrypted file
            if not (os.path.exists(KEY_FILE) and 
                   os.path.exists(CREDENTIALS_FILE) and 
                   os.path.getsize(CREDENTIALS_FILE) > 0):
                return None, None, None

            with open(KEY_FILE, "rb") as key_file:
                key = key_file.read()
            with open(CREDENTIALS_FILE, "rb") as cred_file:
                encrypted_credentials = cred_file.read()
            
            return decrypt_credentials(encrypted_credentials, key)
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return None, None, None

    @staticmethod
    def clear_credentials():
        """Clear stored credentials."""
        try:
            if os.path.exists(CREDENTIALS_FILE):
                os.remove(CREDENTIALS_FILE)
                logger.debug("Credentials file removed.")
            if os.path.exists(KEY_FILE):
                os.remove(KEY_FILE)
                logger.debug("Key file removed.")
            return True
        except Exception as e:
            logger.error(f"Error clearing credentials: {e}")
            return False
