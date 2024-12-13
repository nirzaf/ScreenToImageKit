# ScreenToImageKit

ScreenToImageKit is a Python application that allows users to capture screenshots (both full screen and selected areas) and upload them directly to ImageKit. This tool is designed to be user-friendly and efficient, making it easy to capture and share screenshots.

## Features

- **Area Selection**: Select a specific area on your screen to capture
- **Full Screen Capture**: Capture your entire screen with a single click
- **Direct Upload**: Option to upload screenshots directly to ImageKit without preview
- **Preview Window**: Review your screenshots before uploading (optional)
- **Multiple Configuration Options**:
  - Configure via UI dialog
  - Import configuration from `.env` file
- **Secure Storage**: Encrypted storage of ImageKit credentials
- **System Tray Integration**: Quick access to app features
- **Clipboard Integration**: Automatically copies uploaded image URLs to clipboard

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/nirzaf/ScreenToImageKit.git
   cd ScreenToImageKit
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   python main.py
   ```

## Configuration

You have two ways to configure ImageKit credentials:

### 1. Using the UI
- Click on the "Configure ImageKit" button
- Enter your ImageKit credentials:
  - Private Key
  - Public Key
  - URL Endpoint
- Click "OK" to save

### 2. Using .env File
Create a `.env` file in the root directory with the following content:
```
PRIVATE_KEY=your_private_key
PUBLIC_KEY=your_public_key
URL_ENDPOINT=your_url_endpoint
```
Then either:
- Start the app (it will load credentials automatically)
- Click "Import from .env" button to load credentials manually

## Usage

1. **Capture Area**:
   - Click "Select Area & Capture"
   - Draw a rectangle around the area you want to capture
   - Choose to preview or upload directly using the checkbox

2. **Full Screen Capture**:
   - Click "Capture Full Screen"
   - The app will hide itself during capture
   - Choose to preview or upload directly using the checkbox

3. **Direct Upload**:
   - Check "Upload directly to ImageKit" to skip the preview
   - Uncheck to review screenshots before uploading

4. **Preview Window**:
   - Review your screenshot
   - Click "Upload" to proceed or "Cancel" to discard
   - The URL will be copied to your clipboard after upload

## Future Improvements

- **Enhanced UI**: Improve the user interface for a better user experience
- **Annotation Tools**: Add tools to annotate screenshots before uploading
- **Multiple Image Uploads**: Allow uploading multiple images at once
- **Additional Services**: Integration with other image hosting services
- **Hotkey Support**: Global hotkeys for quick capture

## Contributing

We welcome contributions from the open source community! If you have ideas, suggestions, or bug reports:
1. Open an issue to discuss proposed changes
2. Submit a pull request with your improvements

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
