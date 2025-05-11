"""Main application module for ScreenToImageKit."""

import logging
import tkinter as tk
from src.screentoimagekit.config import ConfigManager
from src.screentoimagekit.services.image_handler import ImageHandler
from src.screentoimagekit.services.imagekit_service import ImageKitService
from src.screentoimagekit.services.temp_file_service import TempFileService
from src.screentoimagekit.ui.main_window import MainWindow
from src.screentoimagekit.ui.system_tray import SystemTray

logger = logging.getLogger(__name__)

class ScreenToImageKit:
    """Main application class."""
    
    def __init__(self):
        """Initialize the application."""
        self._setup_logging()
        logger.info("Initializing ScreenToImageKit")
        
        # Initialize services
        self.temp_file_service = TempFileService()
        self.config_manager = ConfigManager()
        
        # Get API keys from config
        gemini_api_key = self.config_manager.get('GEMINI_API_KEY')
        imagekit_private_key = self.config_manager.get('PRIVATE_KEY')
        imagekit_public_key = self.config_manager.get('PUBLIC_KEY')
        imagekit_url_endpoint = self.config_manager.get('URL_ENDPOINT')
        
        # Initialize services with config
        self.image_handler = ImageHandler(self.temp_file_service, gemini_api_key)
        self.imagekit_service = ImageKitService(
            private_key=imagekit_private_key,
            public_key=imagekit_public_key,
            url_endpoint=imagekit_url_endpoint
        )
        
        # Clean up any leftover temporary files
        self.temp_file_service.cleanup_temp_files()
        
        # Create main window
        self.root = tk.Tk()
        self.main_window = MainWindow(
            self.root,
            self.image_handler,
            self.imagekit_service
        )
        
        # Setup system tray
        self._setup_system_tray()
        
        logger.info("Application initialized successfully")

    def _setup_logging(self):
        """Configure application logging."""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('screenshot_app.log')
            ]
        )

    def _setup_system_tray(self):
        """Setup system tray icon and menu."""
        menu_items = [
            {'text': "Show", 'action': self.main_window.show},
            {'text': "Capture", 'action': self.main_window._handle_area_selection},
            {'text': "Configure", 'action': self.main_window._show_config_dialog},
            {'text': "Exit", 'action': self.exit}
        ]
        
        self.system_tray = SystemTray(
            app_name="Screenshot to ImageKit",
            icon_path="icons/tray.png",
            menu_items=menu_items
        )

    def run(self):
        """Start the application."""
        try:
            logger.info("Starting application main loop")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            # Clean up temporary files on exit
            self.temp_file_service.cleanup_temp_files()
            logger.info("Application shutdown complete")

    def exit(self):
        """Exit the application."""
        try:
            if self.system_tray:
                self.system_tray.stop()
            self.main_window.close()
        except Exception as e:
            logger.error(f"Error during application exit: {e}")
            raise

    def cleanup(self):
        """Clean up application resources."""
        try:
            # Clean up temporary files
            self.temp_file_service.cleanup_temp_files()
            
            # Stop system tray
            if self.system_tray:
                self.system_tray.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def main():
    """Main entry point for the application."""
    try:
        app = ScreenToImageKit()
        app.run()
    except Exception as e:
        logger.error(f"Application failed to start: {e}")

if __name__ == "__main__":
    main()
