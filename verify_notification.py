
import sys
import unittest
from unittest.mock import MagicMock
from pathlib import Path
import json
import os

# Add src to path
sys.path.append(os.getcwd())

from src.utils.assets import AssetStore
from src.utils.email_notifier import EmailNotifier

class TestEmailNotification(unittest.TestCase):
    def setUp(self):
        self.test_file = Path("test_assets.json")
        if self.test_file.exists():
            self.test_file.unlink()
        
        self.store = AssetStore(data_file=self.test_file)
        # Mock the email notifier
        self.store.email_notifier = MagicMock(spec=EmailNotifier)

    def tearDown(self):
        if self.test_file.exists():
            self.test_file.unlink()

    def test_create_laptop_sends_email(self):
        print("\nTesting: Create Laptop should send email...")
        payload = {
            "name": "Test Laptop",
            "asset_type": "Laptop",
            "owner": "John Doe",
            "owner_email": "john@example.com"
        }
        self.store.create_asset(payload)
        
        self.store.email_notifier.send_assignment_email.assert_called_once()
        args = self.store.email_notifier.send_assignment_email.call_args[0]
        self.assertEqual(args[0], "john@example.com")
        self.assertEqual(args[1]['name'], "Test Laptop")
        print("✅ Success: Email sent for new laptop.")

    def test_create_other_asset_no_email(self):
        print("\nTesting: Create Desktop should NOT send email...")
        payload = {
            "name": "Test Desktop",
            "asset_type": "Desktop",
            "owner": "Jane Doe",
            "owner_email": "jane@example.com"
        }
        self.store.create_asset(payload)
        
        self.store.email_notifier.send_assignment_email.assert_not_called()
        print("✅ Success: No email for desktop.")

    def test_update_laptop_owner_sends_email(self):
        print("\nTesting: Update Laptop owner should send email...")
        # Create first
        payload = {
            "name": "Test Laptop",
            "asset_type": "Laptop",
            "owner": "John Doe",
            "owner_email": "john@example.com"
        }
        asset = self.store.create_asset(payload)
        self.store.email_notifier.send_assignment_email.reset_mock()
        
        # Update owner
        update_payload = {
            "owner": "New Owner",
            "owner_email": "new@example.com"
        }
        self.store.update_asset(asset['id'], update_payload)
        
        self.store.email_notifier.send_assignment_email.assert_called_once()
        args = self.store.email_notifier.send_assignment_email.call_args[0]
        self.assertEqual(args[0], "new@example.com")
        print("✅ Success: Email sent on owner change.")

    def test_update_laptop_no_owner_change_no_email(self):
        print("\nTesting: Update Laptop details (not owner) should NOT send email...")
        # Create first
        payload = {
            "name": "Test Laptop",
            "asset_type": "Laptop",
            "owner": "John Doe",
            "owner_email": "john@example.com"
        }
        asset = self.store.create_asset(payload)
        self.store.email_notifier.send_assignment_email.reset_mock()
        
        # Update location
        update_payload = {
            "location": "New Office"
        }
        self.store.update_asset(asset['id'], update_payload)
        
        self.store.email_notifier.send_assignment_email.assert_not_called()
        print("✅ Success: No email when owner unchanged.")

if __name__ == '__main__':
    unittest.main()
