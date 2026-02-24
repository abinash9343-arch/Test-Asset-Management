
import requests
import yaml
from pathlib import Path
import time
import sys

def verify_reset():
    print("Verifying Password Reset Flow...")
    base_url = "http://localhost:8080"
    
    # 1. Check if Forgot Password page loads
    try:
        resp = requests.get(f"{base_url}/forgot-password")
        if resp.status_code == 200 and "Reset Password" in resp.text:
            print("✅ Forgot Password page loaded")
        else:
            print(f"❌ Forgot Password page failed to load. Status: {resp.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error accessing page: {e}")
        sys.exit(1)

    # 2. Capture current config password
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("❌ Config file not found")
        sys.exit(1)
        
    with open(config_path, 'r') as f:
        old_config = yaml.safe_load(f)
        old_password = old_config.get('auth', {}).get('password')
        print(f"ℹ️ Current Password: {old_password}")

    # 3. Trigger Reset
    print("Triggering reset for user 'admin'...")
    session = requests.Session()
    resp = session.post(f"{base_url}/forgot-password", data={'username': 'admin'})
    
    if resp.status_code == 200 and "login" in resp.url and "Reset" in resp.text: # Flask flash messages might appear on login page redirect
       # Note: verifying flash message text in HTML is tricky without parsing, but checking redirect to login is good
       pass
    
    # 4. Verify Config Update
    time.sleep(1) # Give it a moment to write
    with open(config_path, 'r') as f:
        new_config = yaml.safe_load(f)
        new_password = new_config.get('auth', {}).get('password')
        
    if new_password != old_password:
        print(f"✅ Password updated in config.yaml. New Password: {new_password}")
    else:
        print("❌ Password was NOT updated in config.yaml")
        sys.exit(1)

    # 5. Verify Login with New Password
    print("Attempting login with new password...")
    login_resp = session.post(f"{base_url}/login", data={'username': 'admin', 'password': new_password})
    
    if login_resp.status_code == 200 and "Draup IT Agent" in login_resp.text:
        print("✅ Login with new password successful!")
    else:
        print("❌ Login with new password failed")
        sys.exit(1)

    print("\n🎉 Password Reset Verification Passed!")

if __name__ == "__main__":
    verify_reset()
