"""System tray integration for ScreenToImageKit."""

import platform
import threading
import logging
from PIL import Image
import subprocess

logger = logging.getLogger(__name__)

try:
    import pystray
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

class SystemTray:
    """Manages system tray icon and menu."""

    def __init__(self, app_name, icon_path, menu_items):
        self.app_name = app_name
        self.icon_path = icon_path
        self.menu_items = menu_items
        self.icon = None
        self._setup_tray() if PYSTRAY_AVAILABLE else None

    def _setup_tray(self):
        """Setup system tray icon and menu."""
        try:
            # Load icon image
            icon_image = Image.open(self.icon_path)

            # Create menu items
            menu = tuple(
                pystray.MenuItem(
                    text=item['text'],
                    action=item['action']
                ) for item in self.menu_items
            )

            # Create tray icon
            self.icon = pystray.Icon(
                name=self.app_name,
                icon=icon_image,
                title=self.app_name,
                menu=pystray.Menu(*menu)
            )

            # Start in separate thread
            threading.Thread(
                target=self.icon.run,
                daemon=True
            ).start()

            logger.info("System tray icon created successfully")
            return True

        except Exception as e:
            logger.error(f"Error setting up system tray: {e}")
            return False

    def show_notification(self, title, message):
        """Show system notification."""
        if platform.system() == "Darwin":  # macOS
            try:
                subprocess.run([
                    'osascript',
                    '-e',
                    f'display notification "{message}" with title "{title}"'
                ])
            except Exception as e:
                logger.error(f"Error showing notification: {e}")

    def stop(self):
        """Stop the system tray icon."""
        if self.icon:
            try:
                self.icon.stop()
                logger.info("System tray icon stopped")
            except Exception as e:
                logger.error(f"Error stopping system tray: {e}")

    @property
    def is_active(self):
        """Check if system tray is active."""
        return self.icon is not None
