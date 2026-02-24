
import requests
import sys
import time

def verify_login():
    print("Verifying login protection...")
    base_url = "http://localhost:5000"
    
    # Wait for server to start
    for i in range(10):
        try:
            requests.get(base_url)
            break
        except requests.exceptions.ConnectionError:
            print(f"Waiting for server... ({i+1}/10)")
            time.sleep(1)
    else:
        print("❌ Server did not start in time.")
        sys.exit(1)

    # 1. Check root URL (should redirect to login)
    try:
        print(f"Checking {base_url}...")
        response = requests.get(base_url, allow_redirects=False)
        
        if response.status_code == 302:
            print("✅ Root URL redirects (Status 302)")
            location = response.headers.get('Location')
            if '/login' in location:
                print(f"✅ Redirects to: {location}")
            else:
                print(f"❌ Redirects to unexpected location: {location}")
                sys.exit(1)
        elif response.status_code == 401:
             print("✅ Root URL returns 401 Unauthorized")
        else:
            print(f"❌ Root URL returned status {response.status_code}. Expected 302 or 401.")
            # If it returns 200, it means we are NOT protected!
            if response.status_code == 200:
                 print("❌ SECURITY FAIL: Dashboard is accessible without login!")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error checking root URL: {e}")
        sys.exit(1)

    # 2. Check Login URL (should be 200)
    login_url = f"{base_url}/login"
    try:
        print(f"Checking {login_url}...")
        response = requests.get(login_url)
        if response.status_code == 200:
            print("✅ Login page is accessible (Status 200)")
            if "Login" in response.text:
                 print("✅ Login page contains 'Login' text")
            else:
                 print("⚠️ Login page content might be missing 'Login' text")
        else:
            print(f"❌ Login page returned status {response.status_code}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error checking login URL: {e}")
        sys.exit(1)

    print("\n🎉 Authentication verification PASSED!")

if __name__ == "__main__":
    verify_login()
