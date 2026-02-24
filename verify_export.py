
import requests
import sys
import time
import csv
import io
import subprocess
import os
import signal
import yaml

# Configuration
BASE_URL = "http://localhost:5000"
CONFIG_FILE = "config/config.yaml"

def load_config():
    """Load credentials from config file."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = yaml.safe_load(f)
                username = config.get('auth', {}).get('username', 'admin')
                password = config.get('auth', {}).get('password', 'admin123')
                return username, password
    except Exception as e:
        print(f"⚠️ Failed to load config: {e}")
    return 'admin', 'admin123'

def wait_for_server(url, timeout=30):
    """Wait for server to be responsive."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            requests.get(url)
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False

def verify_export():
    print("Verifying Asset Export...")
    
    # Start Server
    print("Starting server...")
    # Use python directly
    server_process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=os.getcwd()
    )
    
    try:
        # Wait for server
        if not wait_for_server(BASE_URL):
            print("❌ Server failed to start.")
            sys.exit(1)
        print("✅ Server started.")

        session = requests.Session()
        username, password = load_config()
        print(f"Using credentials: {username} / {'*' * len(password)}")
        
        # 1. Login
        print("Logging in...")
        login_payload = {'username': username, 'password': password}
        try:
            res = session.post(f"{BASE_URL}/login", data=login_payload)
            # Login usually redirects or returns 200.
            # If we are redirected to '/', and '/' returns 200 (because we are logged in), it's a success?
            # Or if it returns 200 on /login (some apps do that).
            # Let's check session cookie or access protected route.
        except Exception as e:
            print(f"❌ Login request failed: {e}")
            sys.exit(1)
            
        # Check if logged in by accessing a protected route
        res = session.get(f"{BASE_URL}/api/health")
        if res.status_code != 200:
            print("❌ Login failed.")
            print(f"Status: {res.status_code}")
            sys.exit(1)
        print("✅ Login successful.")

        # 2. Create a test asset to ensure data exists
        print("Creating test asset...")
        test_asset = {
            "name": "Export Test Laptop",
            "asset_type": "Laptop",
            "status": "In Use",
            "owner": "Test User",
            "owner_email": "test@example.com"
        }
        res = session.post(f"{BASE_URL}/api/assets", json=test_asset)
        if res.status_code != 200:
            print(f"❌ Failed to create asset: {res.text}")
            sys.exit(1)
        asset_id = res.json().get('asset', {}).get('id')
        print(f"✅ Test asset created: {asset_id}")

        # 3. Download Report
        print("Downloading report...")
        res = session.get(f"{BASE_URL}/api/assets/export")
        
        if res.status_code == 200:
            print("✅ Export endpoint accessible (Status 200)")
            
            # Check headers
            cd = res.headers.get('Content-Disposition', '')
            ct = res.headers.get('Content-Type', '')
            if 'attachment' in cd and 'assets_report.csv' in cd:
                print("✅ Content-Disposition header looks correct.")
            else:
                print(f"⚠️ Unexpected Content-Disposition: {cd}")
                
            if 'text/csv' in ct:
                 print("✅ Content-Type is text/csv.")
            else:
                 print(f"⚠️ Unexpected Content-Type: {ct}")

            # Check content
            content = res.text
            print("--- CSV Content Preview ---")
            print('\n'.join(content.splitlines()[:3])) # Show first 3 lines
            print("---------------------------")
            
            # Parse CSV
            try:
                reader = csv.DictReader(io.StringIO(content))
                rows = list(reader)
                print(f"✅ Parsed {len(rows)} rows from CSV.")
                
                # Find our test asset
                found = False
                for row in rows:
                    if row.get('id') == asset_id:
                        found = True
                        print(f"✅ Found test asset in CSV: {row.get('name')}")
                        break
                
                if not found:
                    print("❌ Test asset NOT found in CSV.")
                else:
                    print("🎉 Verification PASSED!")
                
            except Exception as e:
                print(f"❌ Failed to parse CSV: {e}")

        else:
            print(f"❌ Export failed with status {res.status_code}")
            print(res.text)

        # Clean up
        if asset_id:
            print("Cleaning up...")
            session.delete(f"{BASE_URL}/api/assets/{asset_id}")
            
    finally:
        print("Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()

if __name__ == "__main__":
    verify_export()
