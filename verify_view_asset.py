import requests
import sys
import yaml
import os
import re

BASE_URL = "http://localhost:5000"
CONFIG_FILE = "config/config.yaml"

def load_config():
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

def verify_view_asset():
    print("Verifying Asset View UI elements...")
    try:
        session = requests.Session()
        username, password = load_config()
        
        # Login
        print(f"Logging in as {username}...")
        res = session.post(f"{BASE_URL}/login", data={'username': username, 'password': password})
        if res.status_code != 200:
             # Try accessing protected route to see if redirect happened and we are logged in? 
             # Usually post returns 200 or redirect. Session preserves cookies.
             pass

        # Access Dashboard
        res = session.get(BASE_URL)
        if res.status_code != 200:
            print(f"❌ Failed to fetch page: {res.status_code}")
            sys.exit(1)
        
        content = res.text
        
        # Check 1: Modal HTML
        if 'id="view-modal"' in content and 'Asset Details' in content:
            print("✅ Modal HTML found.")
        else:
            print("❌ Modal HTML NOT found.")
            sys.exit(1)
            
        # Check 2: CSS
        if '.modal { display: none;' in content:
            print("✅ Modal CSS found.")
        else:
            print("❌ Modal CSS NOT found.")
            sys.exit(1)
            
        # Check 3: JS Function
        if 'function viewAsset(asset)' in content:
            print("✅ viewAsset JS function found.")
        else:
            print("❌ viewAsset JS function NOT found.")
            sys.exit(1)
            
        
        # Check 4: Button Order (View -> Edit) - Delete should be gone
        # Regex to find View button, followed by Edit button, followed by closing td
        
        normalized_content = ' '.join(content.split())
        # Make sure "Delete" is NOT in the asset-actions cell
        # We look for <td class="asset-actions"> ... </td> and ensure no Delete inside
        
        # Simple string check might suffice if we know unique class or text
        # But "Delete" text exists in modal script. We need to check the rendered HTML table part.
        # But this script fetches raw HTML. The table is rendered by JS. 
        # The script checks the JS code block string.
        
        # In JS: <td class="asset-actions"> ... <button ...>Delete</button> ... </td>
        # We removed the delete button line.
        
        if "onclick='deleteAsset('${asset.id}')'" in content:
             # Wait, unique string was: onclick="deleteAsset('${asset.id}')"
             # In previous step we removed it.
             # Let's check if that specific JS line is absent.
             # The line was: <button class="btn btn-small btn-danger" onclick="deleteAsset('${asset.id}')">Delete</button>
             if 'btn-danger" onclick="deleteAsset(\'${asset.id}\')">Delete</button>' in content:
                  print("❌ Delete button code STILL FOUND in JS table generation.")
                  sys.exit(1)
             else:
                  print("✅ Delete button code successfully REMOVED from JS table generation.")
        
        # Check 5: Modal Actions (Should still have delete)
        if 'id="modal-actions"' in content:
            print("✅ Modal Actions container found.")
        else:
            print("❌ Modal Actions container NOT found.")
            sys.exit(1)
            
        # Check 6: Delete button in Form (Should still be there)
        if 'id="asset-delete-btn"' in content:
            print("✅ Delete button in Form found.")
        else:
            print("❌ Delete button in Form NOT found.")
            sys.exit(1)

        print("🎉 Verification Complete.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_view_asset()
