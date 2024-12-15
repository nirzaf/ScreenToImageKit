"""Main application window for ScreenToImageKit."""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import pyperclip
from PIL import ImageTk
import win32con
import win32gui
import win32api
import time
from src.screentoimagekit.ui.config_dialog import ConfigDialog
from src.screentoimagekit.ui.preview_window import PreviewWindow
from src.screentoimagekit.ui.selection_window import SelectionWindow
import os

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
        self.success_label = None
        self.screenshot_button = None
        self.fullscreen_button = None
        self.config_button = None
        self.import_env_button = None
        self.direct_upload_var = None
        self.use_gemini_var = None
        
        # Resources
        self.icon_capture = None
        self.icon_config = None
        
        # Hotkey state
        self.last_capture_time = 0
        self.is_capturing = False
        
        # Initialize
        self._setup_window()
        self._load_resources()
        self._create_ui()
        self._load_credentials()
        self._setup_shortcuts()
        
        # Setup message checking
        self.root.bind('<Map>', lambda e: self._setup_message_check())

    def _setup_message_check(self):
        """Setup Windows message checking."""
        def check_messages():
            try:
                current_time = time.time()
                # Check if enough time has passed since last capture (1 second cooldown)
                if current_time - self.last_capture_time >= 1.0 and not self.is_capturing:
                    # Check if Ctrl+W is pressed
                    if win32api.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000 and \
                       win32api.GetAsyncKeyState(ord('W')) & 0x8000:
                        self.last_capture_time = current_time
                        self._quick_capture()
            except Exception as e:
                logger.error(f"Error checking messages: {e}")
            finally:
                # Schedule next check (reduced frequency)
                self.root.after(200, check_messages)
        
        # Start checking messages
        self.root.after(200, check_messages)

    def _quick_capture(self):
        """Handle quick capture with Ctrl + W."""
        if self.is_capturing:
            return
            
        logger.info("Quick capture triggered with Ctrl + W")
        self.is_capturing = True
        
        try:
            # Create selection window with callback
            self.area = None
            def on_selection(coords):
                self.area = coords
            
            selection = SelectionWindow(self.root, on_selection)
            self.root.wait_window(selection.window)  # Wait for selection window to close
            
            if self.area:
                # Capture the selected area
                screenshot_result = self.image_handler.capture_area(self.area)
                temp_path, _ = screenshot_result  # Unpack the tuple, we only need the path
                
                if temp_path:
                    # Upload to ImageKit
                    try:
                        url = self.imagekit_service.upload_file(temp_path)
                        if url:
                            # Show success message at bottom
                            self._show_success("Screenshot uploaded and URL copied to clipboard!")
                        else:
                            self._show_success("Failed to upload screenshot to ImageKit")
                    except ValueError as ve:
                        self._show_status("ImageKit is not configured. Please configure it first.", True)
                    except Exception as e:
                        self._show_status(f"Failed to upload screenshot: {str(e)}", True)
        except Exception as e:
            logger.error(f"Error during quick capture: {e}")
            self._show_status(f"Failed to capture screenshot: {str(e)}", True)
        finally:
            self.is_capturing = False

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
            self._show_status(f"Error loading resources: {str(e)}", True)

    def _create_ui(self):
        """Create main UI elements."""
        logger.debug("Creating main UI elements")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(expand=True, fill="both")

        # Style configuration
        style = ttk.Style()
        style.configure("TButton", padding=6, font=("Arial", 10))
        style.configure("Success.TLabel", foreground="green", font=("Arial", 10))
        style.configure("Error.TLabel", foreground="red", font=("Arial", 10))

        # Info label
        self.info_label = ttk.Label(
            main_frame,
            text="Press Ctrl + W to capture screenshot",
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
        self.direct_upload_var = tk.BooleanVar(value=True)  # Set to True by default
        direct_upload_checkbox = ttk.Checkbutton(
            main_frame,
            text="Upload directly to ImageKit",
            variable=self.direct_upload_var
        )
        direct_upload_checkbox.pack(pady=5)

        # Gemini AI toggle checkbox
        self.use_gemini_var = tk.BooleanVar(value=True)  # Default to True
        gemini_checkbox = ttk.Checkbutton(
            main_frame,
            text="Use Gemini AI for image naming",
            variable=self.use_gemini_var
        )
        gemini_checkbox.pack(pady=5)

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

        # Status label for configuration messages
        self.status_label = ttk.Label(
            main_frame,
            text="",
            font=("Arial", 9)
        )
        self.status_label.pack(pady=10)

        # Success label at the bottom for screenshot messages
        self.success_label = ttk.Label(
            self.root,
            text="",
            style="Success.TLabel",
            padding=(0, 5)
        )
        self.success_label.pack(side=tk.BOTTOM, fill="x", padx=10, pady=5)

        logger.debug("Main UI created successfully")

    def _load_credentials(self):
        """Load ImageKit credentials."""
        try:
            private_key, public_key, url_endpoint = self.config_manager.load_credentials()
            if all([private_key, public_key, url_endpoint]):
                if self.imagekit_service.initialize(private_key, public_key, url_endpoint):
                    self.status_label.configure(
                        text="ImageKit credentials loaded successfully!",
                        style="Success.TLabel"
                    )
                else:
                    self.status_label.configure(
                        text="Error initializing ImageKit service.",
                        style="Error.TLabel"
                    )
            else:
                self.status_label.configure(
                    text="ImageKit credentials not found. Please configure.",
                    style="Error.TLabel"
                )
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            self._show_status(f"Error loading credentials: {str(e)}", True)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Using Windows API for global hotkeys
        pass

    def _show_success(self, message):
        """Show success message in bottom label."""
        self.success_label.configure(style="Success.TLabel", text=message)
        # Clear the message after 3 seconds
        self.root.after(3000, lambda: self.success_label.configure(text=""))

    def _show_status(self, message, is_error=False):
        """Show status message in main status label."""
        self.status_label.config(
            text=message,
            foreground="red" if is_error else "green"
        )

    def _handle_capture(self):
        """Handle screenshot capture button click."""
        if not self.imagekit_service.is_configured:
            self._show_status("Please configure ImageKit credentials.", True)
            return

        try:
            self.root.iconify()
            SelectionWindow(self.root, self._handle_area_selected)
        except Exception as e:
            logger.error(f"Error in capture: {e}")
            self._show_status(f"Failed to start capture: {str(e)}", True)
            self.root.deiconify()

    def _handle_fullscreen_capture(self):
        """Handle full screen capture button click."""
        if not self.imagekit_service.is_configured:
            self._show_status("Please configure ImageKit credentials.", True)
            return

        try:
            # Step 1: Capture screen
            temp_path, screenshot = self.image_handler.capture_fullscreen(window_to_hide=self.root)
            
            if self.direct_upload_var.get():
                # Process synchronously: analyze, rename, upload, cleanup
                self.image_handler.process_and_upload_image(
                    temp_path,
                    use_gemini=self.use_gemini_var.get(),
                    upload_callback=self._handle_upload
                )
            else:
                # Show preview window
                resized_image = self.image_handler.resize_preview(screenshot)
                preview = PreviewWindow(
                    self.root,
                    resized_image,
                    lambda annotated_path=None: self.image_handler.process_and_upload_image(
                        annotated_path or temp_path,
                        use_gemini=self.use_gemini_var.get(),
                        upload_callback=self._handle_upload
                    ),
                    lambda: self.image_handler.cleanup_temp_file(temp_path)
                )
                preview.show()
        except Exception as e:
            logger.error(f"Error in full screen capture: {e}")
            self._show_status(f"Failed to capture full screen: {str(e)}", True)

    def _handle_area_selected(self, coords):
        """Handle area selection completion."""
        self.root.deiconify()
        try:
            logger.debug(f"Selected coordinates: {coords}")
            temp_path, screenshot = self.image_handler.capture_area(coords)
            logger.info(f"Screenshot captured: {temp_path}")
            
            if self.direct_upload_var.get():
                # Process synchronously: analyze, rename, upload, cleanup
                try:
                    logger.debug("Starting direct upload process")
                    self.image_handler.process_and_upload_image(
                        temp_path,
                        use_gemini=self.use_gemini_var.get(),
                        upload_callback=lambda path: self._handle_upload(path)
                    )
                except Exception as e:
                    error_msg = f"Error in image processing: {str(e)}"
                    if hasattr(e, '__traceback__'):
                        import traceback
                        error_msg += f"\nStack trace:\n{''.join(traceback.format_tb(e.__traceback__))}"
                    logger.error(error_msg)
                    self._show_status(f"Error processing image: {str(e)}", True)
                    # Ensure cleanup
                    self.image_handler.cleanup_temp_file(temp_path)
            else:
                # Show preview window
                logger.debug("Showing preview window")
                resized_image = self.image_handler.resize_preview(screenshot)
                preview = PreviewWindow(
                    self.root,
                    resized_image,
                    lambda annotated_path=None: self.image_handler.process_and_upload_image(
                        annotated_path or temp_path,
                        use_gemini=self.use_gemini_var.get(),
                        upload_callback=lambda path: self._handle_upload(path)
                    ),
                    lambda: self.image_handler.cleanup_temp_file(temp_path)
                )
                preview.show()
        except Exception as e:
            error_msg = f"Error handling selected area: {str(e)}"
            if hasattr(e, '__traceback__'):
                import traceback
                error_msg += f"\nStack trace:\n{''.join(traceback.format_tb(e.__traceback__))}"
            logger.error(error_msg)
            self._show_status(f"Failed to process selection: {str(e)}", True)

    def _handle_upload(self, temp_path):
        """Handle screenshot upload."""
        try:
            logger.debug(f"Starting upload for file: {temp_path}")
            if not os.path.exists(temp_path):
                error_msg = f"File not found before upload: {temp_path}"
                logger.error(error_msg)
                self._show_status(error_msg, True)
                return False

            url = self.imagekit_service.upload_file(temp_path)
            if url:
                success_msg = f"Upload successful! URL copied to clipboard: {url}"
                logger.info(success_msg)
                self._show_success(success_msg)
                return True
            
            error_msg = "Upload failed: No URL returned from ImageKit"
            logger.error(error_msg)
            self._show_status(error_msg, True)
            return False
            
        except Exception as e:
            error_msg = f"Error uploading: {str(e)}"
            if hasattr(e, '__traceback__'):
                import traceback
                error_msg += f"\nStack trace:\n{''.join(traceback.format_tb(e.__traceback__))}"
            logger.error(error_msg)
            self._show_status(f"Error: {str(e)}", True)
            return False

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
                    self._show_status("ImageKit configured successfully!")
                else:
                    self._show_status("Error initializing ImageKit service.", True)
            except Exception as e:
                logger.error(f"Error configuring ImageKit: {e}")
                self._show_status(f"Error configuring ImageKit: {str(e)}", True)
        else:
            self._show_status("ImageKit configuration cancelled.", True)

    def _handle_import_env(self):
        """Handle importing configuration from .env file."""
        try:
            private_key, public_key, url_endpoint = self.config_manager.load_env_credentials()
            if all([private_key, public_key, url_endpoint]):
                if self.imagekit_service.initialize(private_key, public_key, url_endpoint):
                    # Save to encrypted storage for future use
                    self.config_manager.save_credentials(private_key, public_key, url_endpoint)
                    self._show_status("Configuration imported from .env successfully!")
                else:
                    self._show_status("Error initializing ImageKit with .env credentials.", True)
            else:
                self._show_status("No valid credentials found in .env file.", True)
        except Exception as e:
            logger.error(f"Error importing .env configuration: {e}")
            self._show_status(f"Error importing .env configuration: {str(e)}", True)

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
