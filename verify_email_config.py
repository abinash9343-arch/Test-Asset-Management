
import sys
import yaml
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

def test_email_config():
    print("="*50)
    print("Email Configuration Verification")
    print("="*50)

    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("❌ Config file not found at config/config.yaml")
        return

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading config file: {e}")
        return

    email_config = config.get('email', {})
    
    if not email_config.get('enabled'):
        print("⚠️ Email is DISABLED in config.")
        return

    smtp_server = email_config.get('smtp_server')
    smtp_port = email_config.get('smtp_port')
    username = email_config.get('username')
    password = email_config.get('password')
    sender_email = email_config.get('sender_email')

    print(f"Server: {smtp_server}:{smtp_port}")
    print(f"User: {username}")
    print(f"Sender: {sender_email}")
    print("-" * 30)

    if "your_email" in username or "example.com" in smtp_server:
        print("❌ It looks like you are still using placeholder values.")
        print("Please update config/config.yaml with your actual email credentials.")
        return

    try:
        print("Attempting to connect to SMTP server...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        print("✅ Connected and started TLS.")
        
        print("Attempting to login...")
        server.login(username, password)
        print("✅ Login successful!")
        
        server.quit()
        print("\n🎉 Configuration is valid!")
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication Failed. Check your username and password.")
        print("   Note: For Gmail, you must use an App Password if 2FA is on.")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_email_config()
