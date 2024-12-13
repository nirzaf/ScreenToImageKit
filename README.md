# ScreenToImageKit

ScreenToImageKit is a Python application that allows users to capture screenshots of selected areas on their screen and upload them directly to ImageKit. This tool is designed to be user-friendly and efficient, making it easy to capture and share screenshots.

## Existing Features

- **Area Selection**: Select a specific area on your screen to capture.
- **Capturing Screenshots**: Capture the selected area and save it as an image file.
- **Configuring ImageKit**: Configure ImageKit credentials to enable uploading of images.
- **Uploading Images to ImageKit**: Upload captured screenshots directly to ImageKit and copy the URL to the clipboard.

## Usage Instructions

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
   python screen-to-imagekit.py
   ```

4. **Configure ImageKit**:
   - Click on the "Configure ImageKit" button.
   - Enter your ImageKit credentials (Private Key, Public Key, URL Endpoint).
   - Click "OK" to save the configuration.

5. **Capture and Upload Screenshot**:
   - Click on the "Select Area & Capture" button.
   - Select the area on your screen that you want to capture.
   - The captured screenshot will be uploaded to ImageKit, and the URL will be copied to your clipboard.

## Future Improvements Roadmap

- **Enhanced UI**: Improve the user interface for a better user experience.
- **Annotation Tools**: Add tools to annotate screenshots before uploading.
- **Multiple Image Uploads**: Allow uploading multiple images at once.
- **Integration with Other Services**: Integrate with other image hosting services.

# ScreenToImageKit

A Python application that captures screenshots and uploads them to ImageKit.

## Publishing New Releases

### Prerequisites
1. Ensure you have a GitHub account and repository access
2. Make sure all your changes are committed and pushed

### Publishing Steps

1. **Update Version Number**
   - Follow semantic versioning (MAJOR.MINOR.PATCH)
   - Example versions: v1.0.0, v1.1.0, v1.2.1

2. **Create and Push a New Tag**
   ```bash
   # Create a new tag
   git tag v1.0.0

   # Push the tag to GitHub
   git push origin v1.0.0
   ```

3. **Fix for Build Error**
   - Replace the expression `${{TITLE}}` with `${{github.event.pull_request.title}}` in the GitHub Actions workflow file `.github/workflows/build-and-release.yml`.

## For Open Source Community Support

We welcome contributions from the open source community to help improve ScreenToImageKit. If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request. Your support and contributions are greatly appreciated!

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
