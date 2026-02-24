# Python Installation Guide

## Python is Required

The IT Agent application requires Python 3.8 or higher. Follow these steps to install it:

## Option 1: Install from Python.org (Recommended)

1. **Download Python:**
   - Go to: https://www.python.org/downloads/
   - Click the big yellow "Download Python" button
   - This will download the latest version

2. **Install Python:**
   - Run the downloaded installer
   - **IMPORTANT:** Check the box "Add Python to PATH" at the bottom
   - Click "Install Now"
   - Wait for installation to complete

3. **Verify Installation:**
   - Open a new terminal/command prompt
   - Type: `python --version`
   - You should see something like: `Python 3.11.x` or `Python 3.12.x`

## Option 2: Install from Microsoft Store

1. **Open Microsoft Store:**
   - Press `Windows Key` and type "Microsoft Store"
   - Open the Microsoft Store app

2. **Search for Python:**
   - Search for "Python 3.11" or "Python 3.12"
   - Click on the official Python app (by Python Software Foundation)

3. **Install:**
   - Click "Install" or "Get"
   - Wait for installation to complete

4. **Verify:**
   - Open a new terminal
   - Type: `python --version`

## After Installing Python

1. **Run the setup script:**
   ```bash
   setup.bat
   ```
   This will install all required dependencies.

2. **Start the application:**
   ```bash
   start.bat
   ```
   Or manually:
   ```bash
   python app.py
   ```

3. **Open your browser:**
   - Go to: http://localhost:5000

## Troubleshooting

### "Python is not recognized"
- Make sure you checked "Add Python to PATH" during installation
- Restart your terminal/command prompt after installation
- Try using `py` instead of `python`: `py app.py`

### "pip is not recognized"
- Use: `python -m pip install -r requirements.txt`
- Or: `py -m pip install -r requirements.txt`

### Still having issues?
- Make sure you installed Python 3.8 or higher
- Try restarting your computer after installation
- Check that Python is in your PATH environment variable

