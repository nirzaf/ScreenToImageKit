from PIL import Image
import os

def resize_icon(input_path, output_path, size):
    with Image.open(input_path) as img:
        # Convert to RGBA if not already
        img = img.convert('RGBA')
        # Use LANCZOS resampling for best quality
        resized_img = img.resize(size, Image.LANCZOS)
        resized_img.save(output_path, 'PNG')

# Directory containing icons
icons_dir = os.path.dirname(os.path.abspath(__file__))

# Resize configurations
icon_configs = {
    'capture.png': (20, 20),  # Slightly larger for button clarity
    'config.png': (20, 20),   # Slightly larger for button clarity
    'tray.png': (16, 16)      # Standard system tray size
}

# Process each icon
for icon_name, size in icon_configs.items():
    input_path = os.path.join(icons_dir, icon_name)
    # Create a backup of original
    backup_path = os.path.join(icons_dir, f'original_{icon_name}')
    if not os.path.exists(backup_path):
        os.rename(input_path, backup_path)
    
    # Resize and save
    resize_icon(backup_path, input_path, size)
    print(f'Resized {icon_name} to {size}px')
