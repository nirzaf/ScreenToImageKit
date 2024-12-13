"""Main application module for ScreenToImageKit."""

import logging
import platform
from src.screentoimagekit.config import ConfigManager
from src.screentoimagekit.utils.imaging import ImageHandler
from src.screentoimagekit.services.imagekit_service import ImageKitService
from src.screentoimagekit.ui.main_window import MainWindow
from src.screentoimagekit.ui.system_tray import SystemTray

logger = logging.getLogger(__name__)

class ScreenToImageKit:
    """Main application class."""

    def __init__(self):
        self._setup_logging()
        logger.info("Initializing ScreenToImageKit")
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.image_handler = ImageHandler()
        self.imagekit_service = ImageKitService()
        
        # Create main window
        self.main_window = MainWindow(
            self.config_manager,
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
            {'text': "Capture", 'action': self.main_window._handle_capture},
            {'text': "Configure", 'action': self.main_window._handle_config},
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
            logger.info("Starting Screenshot to ImageKit application")
            self.main_window.run()
        except Exception as e:
            logger.critical(f"Fatal error in main application: {e}")
            raise
        finally:
            self.cleanup()

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
            if self.system_tray:
                self.system_tray.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def main():
    """Application entry point."""
    try:
        app = ScreenToImageKit()
        app.run()
    except Exception as e:
        logger.critical(f"Application crashed: {e}")
        raise

if __name__ == "__main__":
    main()
