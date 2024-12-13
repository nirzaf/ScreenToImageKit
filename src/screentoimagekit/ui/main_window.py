"""Main application window for ScreenToImageKit."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from PIL import ImageTk
from src.screentoimagekit.ui.config_dialog import ConfigDialog
from src.screentoimagekit.ui.preview_window import PreviewWindow
from src.screentoimagekit.ui.selection_window import SelectionWindow

logger = logging.getLogger(__name__)

class MainWindow:
    """Main application window."""

    def __init__(self, config_manager, image_handler, imagekit_service):
        self.root = tk.Tk()
        self.config_manager = config_manager
        self.image_handler = image_handler
        self.imagekit_service = imagekit_service
        
        # UI elements
        self.info_label = None
        self.status_label = None
        self.screenshot_button = None
        self.fullscreen_button = None
        self.config_button = None
        self.import_env_button = None
        self.direct_upload_var = None
        
        # Resources
        self.icon_capture = None
        self.icon_config = None
        
        # Initialize
        self._setup_window()
        self._load_resources()
        self._create_ui()
        self._load_credentials()

    def _setup_window(self):
        """Setup main window properties."""
        self.root.title("Screenshot to ImageKit")
        self.root.resizable(False, False)
        
        # Center window
        window_width = 400
        window_height = 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def _load_resources(self):
        """Load application icons."""
        try:
            self.icon_capture = tk.PhotoImage(file="icons/capture.png")
            self.icon_config = tk.PhotoImage(file="icons/config.png")
        except Exception as e:
            logger.error(f"Error loading resources: {e}")
            messagebox.showerror("Error", "Failed to load application resources")

    def _create_ui(self):
        """Create main UI elements."""
        logger.debug("Creating main UI elements")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(expand=True, fill="both")

        # Style configuration
        style = ttk.Style()
        style.configure("TButton", padding=6, font=("Arial", 10))

        # Info label
        self.info_label = ttk.Label(
            main_frame,
            text="Click the button below to start area selection",
            font=("Arial", 10)
        )
        self.info_label.pack(pady=10)

        # Screenshot buttons frame
        screenshot_frame = ttk.Frame(main_frame)
        screenshot_frame.pack(pady=10, fill="x")

        # Area screenshot button
        self.screenshot_button = ttk.Button(
            screenshot_frame,
            text="Select Area & Capture",
            command=self._handle_capture,
            image=self.icon_capture,
            compound="left"
        )
        self.screenshot_button.pack(side=tk.LEFT, padx=(0, 5), expand=True, fill="x")

        # Full screen screenshot button
        self.fullscreen_button = ttk.Button(
            screenshot_frame,
            text="Capture Full Screen",
            command=self._handle_fullscreen_capture,
            image=self.icon_capture,
            compound="left"
        )
        self.fullscreen_button.pack(side=tk.LEFT, expand=True, fill="x")

        # Direct upload checkbox
        self.direct_upload_var = tk.BooleanVar()
        direct_upload_checkbox = ttk.Checkbutton(
            main_frame,
            text="Upload directly to ImageKit",
            variable=self.direct_upload_var
        )
        direct_upload_checkbox.pack(pady=5)

        # Status label
        self.status_label = ttk.Label(
            main_frame,
            text="",
            font=("Arial", 9)
        )
        self.status_label.pack(pady=10)

        # Config frame
        config_frame = ttk.Frame(main_frame)
        config_frame.pack(pady=10, fill="x")

        # Config button
        self.config_button = ttk.Button(
            config_frame,
            text="Configure ImageKit",
            command=self._handle_config,
            image=self.icon_config,
            compound="left"
        )
        self.config_button.pack(side=tk.LEFT, padx=(0, 5), expand=True, fill="x")

        # Import from .env button
        self.import_env_button = ttk.Button(
            config_frame,
            text="Import from .env",
            command=self._handle_import_env
        )
        self.import_env_button.pack(side=tk.LEFT, expand=True, fill="x")

        logger.debug("Main UI created successfully")

    def _load_credentials(self):
        """Load ImageKit credentials."""
        try:
            private_key, public_key, url_endpoint = self.config_manager.load_credentials()
            if all([private_key, public_key, url_endpoint]):
                if self.imagekit_service.initialize(private_key, public_key, url_endpoint):
                    self.status_label.config(
                        text="ImageKit credentials loaded successfully!",
                        foreground="green"
                    )
                else:
                    self.status_label.config(
                        text="Error initializing ImageKit service.",
                        foreground="red"
                    )
            else:
                self.status_label.config(
                    text="ImageKit credentials not found. Please configure.",
                    foreground="red"
                )
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            self.status_label.config(
                text=f"Error loading credentials: {e}",
                foreground="red"
            )

    def _handle_capture(self):
        """Handle screenshot capture button click."""
        if not self.imagekit_service.is_configured:
            self.status_label.config(
                text="Please configure ImageKit credentials.",
                foreground="red"
            )
            return

        try:
            self.root.iconify()
            SelectionWindow(self.root, self._handle_area_selected)
        except Exception as e:
            logger.error(f"Error in capture: {e}")
            messagebox.showerror("Error", f"Failed to start capture: {str(e)}")
            self.root.deiconify()

    def _handle_fullscreen_capture(self):
        """Handle full screen capture button click."""
        if not self.imagekit_service.is_configured:
            self.status_label.config(
                text="Please configure ImageKit credentials.",
                foreground="red"
            )
            return

        try:
            temp_path, screenshot = self.image_handler.capture_fullscreen(window_to_hide=self.root)
            resized_image = self.image_handler.resize_preview(screenshot)
            
            if self.direct_upload_var.get():
                # Direct upload without preview
                self._handle_upload(temp_path)
            else:
                # Show preview window
                PreviewWindow(
                    self.root,
                    resized_image,
                    lambda: self._handle_upload(temp_path),
                    lambda: self._handle_cancel(temp_path)
                )
        except Exception as e:
            logger.error(f"Error in full screen capture: {e}")
            messagebox.showerror("Error", f"Failed to capture full screen: {str(e)}")

    def _handle_area_selected(self, coords):
        """Handle area selection completion."""
        self.root.deiconify()
        try:
            temp_path, screenshot = self.image_handler.capture_area(coords)
            resized_image = self.image_handler.resize_preview(screenshot)
            
            if self.direct_upload_var.get():
                # Direct upload without preview
                self._handle_upload(temp_path)
            else:
                # Show preview window
                PreviewWindow(
                    self.root,
                    resized_image,
                    lambda: self._handle_upload(temp_path),
                    lambda: self._handle_cancel(temp_path)
                )
        except Exception as e:
            logger.error(f"Error handling selected area: {e}")
            messagebox.showerror("Error", f"Failed to process selection: {str(e)}")

    def _handle_upload(self, temp_path):
        """Handle screenshot upload."""
        try:
            url = self.imagekit_service.upload_file(temp_path)
            self.status_label.config(
                text=f"Upload successful! URL copied to clipboard: {url}",
                foreground="green"
            )
        except Exception as e:
            logger.error(f"Error uploading: {e}")
            self.status_label.config(
                text=f"Error: {str(e)}",
                foreground="red"
            )
        finally:
            self.image_handler.cleanup_temp_file(temp_path)

    def _handle_cancel(self, temp_path):
        """Handle preview cancellation."""
        self.image_handler.cleanup_temp_file(temp_path)

    def _handle_config(self):
        """Handle configuration button click."""
        dialog = ConfigDialog(self.root)
        self.root.wait_window(dialog)

        if dialog.result:
            try:
                if self.imagekit_service.initialize(
                    dialog.result['private_key'],
                    dialog.result['public_key'],
                    dialog.result['url_endpoint']
                ):
                    self.config_manager.save_credentials(
                        dialog.result['private_key'],
                        dialog.result['public_key'],
                        dialog.result['url_endpoint']
                    )
                    self.status_label.config(
                        text="ImageKit configured successfully!",
                        foreground="green"
                    )
                else:
                    self.status_label.config(
                        text="Error initializing ImageKit service.",
                        foreground="red"
                    )
            except Exception as e:
                logger.error(f"Error configuring ImageKit: {e}")
                self.status_label.config(
                    text=f"Error configuring ImageKit: {str(e)}",
                    foreground="red"
                )
        else:
            self.status_label.config(
                text="ImageKit configuration cancelled.",
                foreground="red"
            )

    def _handle_import_env(self):
        """Handle importing configuration from .env file."""
        try:
            private_key, public_key, url_endpoint = self.config_manager.load_env_credentials()
            if all([private_key, public_key, url_endpoint]):
                if self.imagekit_service.initialize(private_key, public_key, url_endpoint):
                    # Save to encrypted storage for future use
                    self.config_manager.save_credentials(private_key, public_key, url_endpoint)
                    self.status_label.config(
                        text="Configuration imported from .env successfully!",
                        foreground="green"
                    )
                else:
                    self.status_label.config(
                        text="Error initializing ImageKit with .env credentials.",
                        foreground="red"
                    )
            else:
                self.status_label.config(
                    text="No valid credentials found in .env file.",
                    foreground="red"
                )
        except Exception as e:
            logger.error(f"Error importing .env configuration: {e}")
            self.status_label.config(
                text=f"Error importing .env configuration: {str(e)}",
                foreground="red"
            )

    def run(self):
        """Start the application main loop."""
        try:
            logger.info("Starting application main loop")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            raise

    def hide(self):
        """Hide the main window."""
        self.root.withdraw()

    def show(self):
        """Show and focus the main window."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def close(self):
        """Close the application window."""
        self.root.quit()
