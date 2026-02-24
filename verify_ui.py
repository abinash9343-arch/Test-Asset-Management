
import requests
import sys
import time

def verify_ui():
    print("Verifying UI elements...")
    base_url = "http://localhost:8080"
    login_url = f"{base_url}/login"
    
    # Wait for server
    for i in range(10):
        try:
            requests.get(base_url)
            break
        except requests.exceptions.ConnectionError:
            print(f"Waiting for server... ({i+1}/10)")
            time.sleep(1)
    else:
        print("❌ Server did not start.")
        sys.exit(1)

    # Check Login Page Title
    print("Checking Login Page Branding...")
    resp = requests.get(login_url)
    if "Draup IT Agent" in resp.text:
        print("✅ Correct Branding found on Login Page")
    else:
        print("❌ Branding missing on Login Page")
        sys.exit(1)

    # Login
    session = requests.Session()
    try:
        print("Logging in...")
        # Get CSRF token if needed (not implemented yet, but good practice)
        response = session.post(login_url, data={'username': 'admin', 'password': 'admin123'})
        
        if response.status_code == 200 and "Draup IT Agent" in response.text:
            print("✅ Login successful")
            
            # Check for Logout button
            if '/logout' in response.text:
                print("✅ Logout link found in dashboard")
            else:
                print("❌ Logout link NOT found in dashboard HTML")
                print("HTML Snippet:", response.text[:1000]) # Print first 1000 chars to debug
                sys.exit(1)
                
            # Check for User info
            if 'User:' in response.text or '👤' in response.text: # I added a visual icon
                print("✅ User info display found")
            else:
                print("⚠️ User info display might be missing")

        else:
            print(f"❌ Login failed or didn't redirect to dashboard. Status: {response.status_code}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    print("\n🎉 UI verification PASSED!")

if __name__ == "__main__":
    verify_ui()
