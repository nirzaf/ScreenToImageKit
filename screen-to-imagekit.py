import logging
import os
import tkinter as tk
import traceback
from datetime import datetime
from tkinter import messagebox, simpledialog, ttk
import secrets
from cryptography.fernet import Fernet
import pyperclip
from PIL import ImageGrab, ImageTk
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
import platform

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console handler
        logging.FileHandler('screenshot_app.log')  # File handler
    ]
)
logger = logging.getLogger(__name__)

CREDENTIALS_FILE = "imagekit_credentials.dat"
KEY_FILE = "encryption_key.key"


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
        private_key, public_key, url_endpoint = decrypted_credentials.split(':')
        return private_key, public_key, url_endpoint
    except Exception as e:
        logger.error(f"Error decrypting credentials: {e}")
        return None, None, None


class ScreenshotApp:
    def __init__(self):
        logger.info("Initializing ScreenshotApp")
        self.root = tk.Tk()
        self.root.title("Screenshot to ImageKit")
        self.root.withdraw()  # Hide main window initially
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)  # Handle close button
        self.root.resizable(False, False)  # Disable resizing
        # Initialize variables
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.selection_window = None
        self.imagekit = None
        self.temp_path = None
        self.preview_window = None
        self.preview_image = None
        self.clipboard_button_visible = False  # Flag for button visibility

        # Load icons
        self.icon_capture = self.load_icon("icons/capture.png")
        self.icon_config = self.load_icon("icons/config.png")
        self.icon_tray = self.load_icon("icons/tray.png")

        # Create system tray icon
        self.tray_icon = tk.PhotoImage(file="icons/tray.png")  # Load icon for tray
        self.tray = tk.Menu(self.root, tearoff=0)
        self.tray.add_command(label="Show", command=self.show_window)
        self.tray.add_command(label="Capture", command=self.start_selection)
        self.tray.add_command(label="Config", command=self.configure_imagekit)
        self.tray.add_separator()
        self.tray.add_command(label="Exit", command=self.exit_app)
        self.tray_icon_menu = tk.Menu(self.root, tearoff=0)
        self.tray_icon_menu.add_command(label="Show", command=self.show_window)
        self.tray_icon_menu.add_command(label="Capture", command=self.start_selection)
        self.tray_icon_menu.add_command(label="Config", command=self.configure_imagekit)
        self.tray_icon_menu.add_separator()
        self.tray_icon_menu.add_command(label="Exit", command=self.exit_app)
        self.tray_icon = self.create_tray_icon()

        # Create main UI
        self.create_main_ui()

        # Load or get credentials AFTER UI is created
        self.load_credentials()

        logger.info("Application initialized successfully")

    def load_icon(self, path):
        try:
            return tk.PhotoImage(file=path)
        except tk.TclError as e:
            logger.error(f"Error loading icon '{path}': {e}")
            return None

    def create_tray_icon(self):
        try:
            if platform.system() == "Darwin":
                icon = self.tray_icon
            else:
                import pystray
                icon = pystray.Icon("ScreenshotApp", self.tray_icon, "Screenshot to ImageKit", self.tray_icon_menu)
                icon.run_async()
            return icon
        except Exception as e:
            logger.error(f"Error creating tray icon: {e}")
            return None

    def hide_window(self):
        self.root.withdraw()  # Hide main window
        if platform.system() == "Darwin":
            self.show_tray_message("Screenshot to ImageKit", "Running in system tray")

    def show_window(self):
        self.root.deiconify()  # Show main window
        self.root.lift() # Ensure window is on top
    
    def show_tray_message(self, title, message):
        if platform.system() == "Darwin":
           import subprocess
           subprocess.run(['osascript', '-e', f'display notification "{message}" with title "{title}"'])

    def exit_app(self):
        if self.tray_icon and platform.system() != "Darwin":
             self.tray_icon.stop()
        self.root.destroy()


    def create_main_ui(self):
        logger.debug("Creating main UI elements")
        # Create and pack widgets
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill="both")

        # Labels and buttons using ttk for a more modern look
        style = ttk.Style()
        style.configure("TButton", padding=6, font=("Arial", 10))  # Setting global style

        self.info_label = ttk.Label(main_frame, text="Click the button below to start area selection", font=("Arial", 10))
        self.info_label.pack(pady=10)

        self.screenshot_button = ttk.Button(main_frame, text="Select Area & Capture", command=self.start_selection,
                                            image=self.icon_capture, compound="left")
        self.screenshot_button.pack(pady=10, fill="x")

        self.status_label = ttk.Label(main_frame, text="", font=("Arial", 9))
        self.status_label.pack(pady=10)

        self.config_button = ttk.Button(main_frame, text="Configure ImageKit", command=self.configure_imagekit,
                                         image=self.icon_config, compound="left")
        self.config_button.pack(pady=10, fill="x")
        logger.debug("Main UI created successfully")

    def configure_imagekit(self):
        dialog = ConfigDialog(self.root)
        self.root.wait_window(dialog)

        if dialog.result:
            try:
                # Initialize ImageKit instance first to validate credentials
                self.imagekit = ImageKit(
                    private_key=dialog.result['private_key'],
                    public_key=dialog.result['public_key'],
                    url_endpoint=dialog.result['url_endpoint']
                )

                # If initialization successful, save the credentials
                if not os.path.exists(KEY_FILE):
                    key = Fernet.generate_key()
                    with open(KEY_FILE, "wb") as key_file:
                        key_file.write(key)
                else:
                    with open(KEY_FILE, "rb") as key_file:
                        key = key_file.read()

                encrypted_credentials = encrypt_credentials(
                    dialog.result['private_key'],
                    dialog.result['public_key'],
                    dialog.result['url_endpoint'],
                    key
                )
                with open(CREDENTIALS_FILE, "wb") as cred_file:
                    cred_file.write(encrypted_credentials)

                self.status_label.config(text="ImageKit configured successfully!", fg="green")
            except Exception as e:
                logger.error(f"Error configuring ImageKit: {e}")
                self.status_label.config(text=f"Error configuring ImageKit: {str(e)}", fg="red")
                self.imagekit = None
        else:
            self.status_label.config(text="ImageKit configuration cancelled.", fg="red")

    def load_credentials(self):
        try:
            if os.path.exists(KEY_FILE) and os.path.exists(CREDENTIALS_FILE) and os.path.getsize(CREDENTIALS_FILE) > 0:
                with open(KEY_FILE, "rb") as key_file:
                    key = key_file.read()
                with open(CREDENTIALS_FILE, "rb") as cred_file:
                    encrypted_credentials = cred_file.read()
                private_key, public_key, url_endpoint = decrypt_credentials(encrypted_credentials, key)
                if private_key and public_key and url_endpoint:
                    self.imagekit = ImageKit(private_key=private_key, public_key=public_key, url_endpoint=url_endpoint)
                    self.status_label.config(text="ImageKit credentials loaded successfully!", fg="green")
                else:
                    self.status_label.config(text="Error loading ImageKit credentials.", fg="red")
            else:
                self.status_label.config(text="ImageKit credentials not found. Please configure.", fg="red")
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            self.status_label.config(text=f"Error loading credentials: {e}", fg="red")

    def start_selection(self):
        if self.imagekit is None:
            self.status_label.config(text="Please configure ImageKit credentials.", fg="red")
            return
        logger.info("Starting area selection")
        try:
            self.root.iconify()  # minimize the root window
            self.selection_window = tk.Toplevel(self.root)
            self.selection_window.attributes('-fullscreen', True, '-alpha', 0.3)
            self.selection_window.configure(background='grey')

            self.selection_window.bind('<Button-1>', self.begin_rect)
            self.selection_window.bind('<B1-Motion>', self.update_rect)
            self.selection_window.bind('<ButtonRelease-1>', self.end_rect)

            # Create canvas for drawing selection rectangle
            self.canvas = tk.Canvas(self.selection_window, highlightthickness=0)
            self.canvas.pack(fill='both', expand=True)
            logger.debug("Selection window created successfully")

        except Exception as e:
            error_msg = f"Error in area selection: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            messagebox.showerror("Error", f"Failed to start area selection: {str(e)}")
            self.root.deiconify()

    def begin_rect(self, event):
        logger.debug(f"Beginning rectangle selection at coordinates ({event.x}, {event.y})")
        self.start_x = event.x
        self.start_y = event.y
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=2
        )

    def update_rect(self, event):
        if self.current_rect and self.start_x is not None and self.start_y is not None:
            self.canvas.coords(
                self.current_rect,
                self.start_x, self.start_y,
                event.x, event.y
            )

    def end_rect(self, event):
        if self.current_rect:
            logger.info("Ending rectangle selection")
            coords = self.canvas.coords(self.current_rect)
            logger.debug(f"Selected coordinates: {coords}")
            if self.selection_window:
                self.selection_window.destroy()
            self.root.deiconify()
            self.capture_area(coords)

    def capture_area(self, coords):
        logger.info("Capturing selected area")
        try:
            x1, y1, x2, y2 = map(int, coords)
            # Ensure coordinates are in correct order
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)

            logger.debug(f"Capturing area with coordinates: ({x1}, {y1}, {x2}, {y2})")

            # Capture the selected area
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))

            # Save temporarily
            self.temp_path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot.save(self.temp_path)
            logger.info(f"Screenshot saved temporarily as {self.temp_path}")

            # Show preview
            self.show_preview(self.temp_path)

        except Exception as e:
            error_msg = f"Error capturing area: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            messagebox.showerror("Error", f"Failed to capture area: {str(e)}")

    def show_preview(self, file_path):
        logger.info("Showing preview window")
        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.title("Screenshot Preview")
        self.preview_window.transient(self.root)
        self.preview_window.grab_set()
        self.preview_window.focus_force() # bring preview window to the front
        self.preview_window.resizable(False, False) # prevent resizing

        try:
            img = ImageGrab.grab()
            img = ImageGrab.grab(bbox = ImageGrab.grab().getbbox())
            img = img.resize((int(img.width/2),int(img.height/2)),ImageGrab.Resampling.LANCZOS)
            self.preview_image = ImageTk.PhotoImage(img)
            preview_label = tk.Label(self.preview_window, image=self.preview_image)
            preview_label.image = self.preview_image # keep a reference
            preview_label.pack(padx=10, pady=10)

            # Frame for buttons
            button_frame = tk.Frame(self.preview_window)
            button_frame.pack(pady=10)

            upload_button = ttk.Button(button_frame, text="Upload", command=self.upload_and_close)
            upload_button.pack(side=tk.LEFT, padx=5)

            cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel_preview)
            cancel_button.pack(side=tk.LEFT, padx=5)

        except Exception as e:
             logger.error(f"Error showing preview window: {e}")
             messagebox.showerror("Error", f"Failed to show preview: {str(e)}")

    def upload_and_close(self):
          if self.temp_path:
                self.upload_to_imagekit(self.temp_path)
                self.cleanup()
          if self.preview_window:
              self.preview_window.destroy()
              self.preview_window = None
    def cancel_preview(self):
          self.cleanup()
          if self.preview_window:
             self.preview_window.destroy()
             self.preview_window = None

    def cleanup(self):
        if self.temp_path and os.path.exists(self.temp_path):
             os.remove(self.temp_path)
             logger.debug(f"Temporary file {self.temp_path} removed")
             self.temp_path = None

    def upload_to_imagekit(self, file_path):
        logger.info(f"Uploading file: {file_path}")
        try:
            # Create upload options using the SDK's model
            options = UploadFileRequestOptions(
                response_fields=["is_private_file", "tags"],
                tags=["screenshot"],
                folder="/screenshots"  # Specify the folder in options
            )

            # Upload using ImageKit SDK
            with open(file_path, 'rb') as file:
                upload = self.imagekit.upload_file(
                    file=file,
                    file_name=os.path.basename(file_path),
                    options=options
                )

                if upload and hasattr(upload, 'url'):
                    # Copy URL to clipboard
                    pyperclip.copy(upload.url)
                    success_msg = f"Upload successful! URL copied to clipboard: {upload.url}"
                    logger.info(success_msg)
                    self.status_label.config(text=success_msg, fg="green")
                else:
                    raise Exception("Upload failed: Invalid response from ImageKit")

        except Exception as e:
            error_msg = f"Error uploading to ImageKit: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            self.status_label.config(text=f"Error: {str(e)}", fg="red")

    def run(self):
        logger.info("Starting application main loop")
        self.root.mainloop()


class ConfigDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("ImageKit Configuration")
        self.result = None
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Create form fields
        tk.Label(self, text="Private Key:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.private_key = tk.Entry(self, width=50)
        self.private_key.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self, text="Public Key:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.public_key = tk.Entry(self, width=50)
        self.public_key.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self, text="URL Endpoint:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.url_endpoint = tk.Entry(self, width=50)
        self.url_endpoint.grid(row=2, column=1, padx=5, pady=5)

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        tk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)

        # Center the dialog
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        # Set focus on first field
        self.private_key.focus_set()

    def ok_clicked(self):
        self.result = {
            'private_key': self.private_key.get(),
            'public_key': self.public_key.get(),
            'url_endpoint': self.url_endpoint.get()
        }
        self.destroy()

    def cancel_clicked(self):
        self.destroy()

if __name__ == "__main__":
    try:
        logger.info("Starting Screenshot to ImageKit application")
        app = ScreenshotApp()
        app.run()
    except Exception as e:
        error_msg = f"Fatal error in main application: {str(e)}\n{traceback.format_exc()}"
        logger.critical(error_msg)
        messagebox.showerror("Fatal Error", f"Application crashed: {str(e)}")