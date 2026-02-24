"""User storage and management for Draup Asset Management."""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

USER_DATA_FILE = Path("users.json")

@dataclass
class UserData:
    """Represents a single user account."""
    username: str
    password: str
    role: str  # 'admin' or 'viewer'
    created_at: str = ""

class UserStore:
    """File-based storage for user accounts."""

    def __init__(self, data_file: Path = USER_DATA_FILE):
        self.data_file = data_file
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Ensure users file exists with a default admin account."""
        if not self.data_file.exists():
            # Initial default admin from config might be migrated later, 
            # but for now we start with a standard set.
            default_admin = {
                "username": "admin",
                "password": "z&0CI$xTSM%p", # This was the latest generated admin password
                "role": "admin",
                "created_at": datetime.utcnow().isoformat()
            }
            self._write_all([default_admin])

    def _read_all(self) -> List[Dict[str, Any]]:
        try:
            if not self.data_file.exists():
                return []
            with self.data_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _write_all(self, users: List[Dict[str, Any]]) -> None:
        self.data_file.write_text(json.dumps(users, indent=2), encoding="utf-8")

    def list_users(self) -> List[Dict[str, Any]]:
        """Return all users (sanitized)."""
        users = self._read_all()
        # Hide passwords when listing
        return [{k: v for k, v in u.items() if k != 'password'} for u in users]

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Return a single user by username."""
        for user in self._read_all():
            if user.get("username") == username:
                return user
        return None

    def validate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Validate credentials and return user info if successful."""
        user = self.get_user(username)
        if user and user.get("password") == password:
            return user
        return None

    def create_user(self, username: str, password: str, role: str) -> Optional[Dict[str, Any]]:
        """Create a new user account."""
        if self.get_user(username):
            return None # Already exists
        
        new_user = {
            "username": username.strip(),
            "password": password.strip(),
            "role": role.strip() or "viewer",
            "created_at": datetime.utcnow().isoformat()
        }
        
        users = self._read_all()
        users.append(new_user)
        self._write_all(users)
        return {k: v for k, v in new_user.items() if k != 'password'}

    def update_password(self, username: str, new_password: str) -> bool:
        """Update a user's password."""
        users = self._read_all()
        updated = False
        for user in users:
            if user.get("username") == username:
                user["password"] = new_password
                updated = True
                break
        if updated:
            self._write_all(users)
        return updated

    def delete_user(self, username: str) -> bool:
        """Delete a user account."""
        if username == "admin":
            return False # Prevent deleting the primary admin
            
        users = self._read_all()
        new_users = [u for u in users if u.get("username") != username]
        if len(new_users) == len(users):
            return False
            
        self._write_all(new_users)
        return True
