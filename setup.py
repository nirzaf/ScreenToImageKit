"""Setup script for ScreenToImageKit."""

from setuptools import setup, find_packages

setup(
    name="screentoimagekit",
    version="1.1.0",  # Updated version for new features
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pillow",
        "pyperclip",
        "imagekitio",
        "cryptography",
        "pystray",
        "python-dotenv",
        "keyboard"  # Added for global hotkeys
    ],
    entry_points={
        "console_scripts": [
            "screentoimagekit=screentoimagekit.app:main",
        ],
    },
    author="nirzaf",
    description="A Python application for capturing and uploading screenshots to ImageKit",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/nirzaf/ScreenToImageKit",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
