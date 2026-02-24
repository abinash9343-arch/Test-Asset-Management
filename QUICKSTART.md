# Quick Start Guide

## ✅ All Files Created Successfully!

The Draup Asset Management application is ready. Follow these steps to run it:

## 🚀 Quick Start (Easiest Method)

**Just double-click these files in order:**

1. **First time setup:** Double-click `setup.bat`
   - This will check for Python and install dependencies

2. **Start the app:** Double-click `start.bat`
   - This will start the web server

3. **Open browser:** Go to http://localhost:5000

---

## Step 1: Install Python (if not already installed)

1. Download Python from: https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Verify installation by opening a new terminal and running:
   ```bash
   python --version
   ```

## Step 2: Install Dependencies

Open a terminal in this directory and run:

```bash
pip install -r requirements.txt
```

Or if that doesn't work:

```bash
python -m pip install -r requirements.txt
```

## Step 3: Start the Application

```bash
python app.py
```

## Step 4: Open in Browser

Once the server starts, open your browser and go to:

**http://localhost:5000**

## What You'll See

- 🖥️ **System Health Dashboard** - Real-time health monitoring
- 📊 **Agent Metrics** - Performance statistics
- 🔧 **Available Tasks** - Execute diagnostic tasks
- 🚀 **Quick Actions** - Run full diagnostics

## Troubleshooting

### If Python is not found:
- Make sure Python is installed
- Add Python to your system PATH
- Try using `py` command instead: `py app.py`

### If pip is not found:
- Use: `python -m pip install -r requirements.txt`
- Or: `py -m pip install -r requirements.txt`

### If port 5000 is in use:
- The app will try to use port 5000 by default
- You can change it by editing `app.py` or passing a port number

## Need Help?

Check the `README.md` file for more detailed information.

