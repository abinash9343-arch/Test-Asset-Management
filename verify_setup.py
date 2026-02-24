"""Verification script to check if everything is set up correctly"""
import sys

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("✗ Python 3.8 or higher is required")
        return False
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'yaml', 'psutil', 'requests', 'dotenv', 'colorama', 'flask', 'flask_cors'
    ]
    missing = []
    
    for package in required_packages:
        try:
            if package == 'yaml':
                import yaml
            elif package == 'dotenv':
                import dotenv
            elif package == 'flask_cors':
                import flask_cors
            else:
                __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is NOT installed")
            missing.append(package)
    
    return len(missing) == 0, missing

def check_files():
    """Check if required files exist"""
    import os
    from pathlib import Path
    
    required_files = [
        'app.py',
        'requirements.txt',
        'src/agent/it_agent.py',
        'src/agent/tasks.py',
        'src/diagnostics/logger.py',
        'src/diagnostics/health_check.py',
        'src/diagnostics/monitor.py',
        'src/utils/config.py',
        'config/config.yaml'
    ]
    
    missing = []
    for file in required_files:
        if Path(file).exists():
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} is missing")
            missing.append(file)
    
    return len(missing) == 0, missing

def main():
    print("=" * 50)
    print("IT Agent - Setup Verification")
    print("=" * 50)
    print()
    
    # Check Python version
    print("Checking Python version...")
    python_ok = check_python_version()
    print()
    
    if not python_ok:
        print("Please install Python 3.8 or higher")
        print("See INSTALL_PYTHON.md for instructions")
        return
    
    # Check dependencies
    print("Checking dependencies...")
    deps_ok, missing_deps = check_dependencies()
    print()
    
    if not deps_ok:
        print(f"Missing packages: {', '.join(missing_deps)}")
        print("Run: pip install -r requirements.txt")
        print()
    
    # Check files
    print("Checking files...")
    files_ok, missing_files = check_files()
    print()
    
    # Summary
    print("=" * 50)
    print("Summary")
    print("=" * 50)
    
    if python_ok and deps_ok and files_ok:
        print("✓ Everything is set up correctly!")
        print()
        print("You can now start the application:")
        print("  python app.py")
        print()
        print("Then open your browser at: http://localhost:5000")
    else:
        print("✗ Setup incomplete")
        if not python_ok:
            print("  - Python needs to be installed")
        if not deps_ok:
            print(f"  - Install missing packages: {', '.join(missing_deps)}")
        if not files_ok:
            print(f"  - Missing files: {', '.join(missing_files)}")
    
    print()

if __name__ == "__main__":
    main()

