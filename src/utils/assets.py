"""Simple IT Asset storage for the IT Agent dashboard."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
from src.utils.email_notifier import EmailNotifier


DATA_FILE = Path("assets.json")


@dataclass
class Asset:
    """Represents a single IT asset."""

    id: str
    name: str
    asset_type: str
    owner: str = ""
    owner_email: str = ""
    department: str = ""
    status: str = "In Use"  # In Use, In Stock, Retired, Repair
    location: str = ""
    purchase_date: str = ""
    warranty_expiry: str = ""
    serial_number: str = ""
    employee_code: str = ""
    configuration: str = ""
    tags: str = ""  # comma separated
    accessories: str = ""
    invoice: str = ""


class AssetStore:
    """File-based storage for IT assets."""

    def __init__(self, data_file: Path = DATA_FILE):
        self.data_file = data_file
        self.email_notifier = EmailNotifier()
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Ensure data file exists."""
        if not self.data_file.exists():
            self._write_all([])

    def _read_all(self) -> List[Dict[str, Any]]:
        try:
            with self.data_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            return []
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            # Corrupted file – don't crash the app
            return []

    def _write_all(self, items: List[Dict[str, Any]]) -> None:
        self.data_file.write_text(json.dumps(items, indent=2), encoding="utf-8")

    # Public API ---------------------------------------------------------

    def list_assets(self) -> List[Dict[str, Any]]:
        """Return all assets."""
        return self._read_all()

    def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Return a single asset by id."""
        for asset in self._read_all():
            if asset.get("id") == asset_id:
                return asset
        return None

    def create_asset(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create and store a new asset."""
        now = datetime.utcnow().isoformat()
        asset = Asset(
            id=str(uuid4()),
            name=payload.get("name", "").strip(),
            asset_type=payload.get("asset_type", "").strip(),
            owner=payload.get("owner", "").strip(),
            owner_email=payload.get("owner_email", "").strip(),
            department=payload.get("department", "").strip(),
            status=payload.get("status", "In Use").strip() or "In Use",
            location=payload.get("location", "").strip(),
            purchase_date=payload.get("purchase_date", "").strip(),
            warranty_expiry=payload.get("warranty_expiry", "").strip(),
            serial_number=payload.get("serial_number", "").strip(),
            employee_code=payload.get("employee_code", "").strip(),
            configuration=payload.get("configuration", "").strip(),
            tags=payload.get("tags", "").strip(),
            accessories=payload.get("accessories", "").strip(),
            invoice=payload.get("invoice", "").strip(),
        )
        data = self._read_all()
        asset_dict = asdict(asset)
        asset_dict["created_at"] = now
        asset_dict["updated_at"] = now
        data.append(asset_dict)
        self._write_all(data)
        
        # Check if email notification is needed
        if asset.asset_type.lower() == "laptop" and asset.owner and asset.owner_email:
            self.email_notifier.send_assignment_email(asset.owner_email, asset_dict)
            
        return asset_dict

    def update_asset(self, asset_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing asset."""
        data = self._read_all()
        updated = None
        for idx, item in enumerate(data):
            if item.get("id") == asset_id:
                original_owner = item.get("owner")
                # Only update known fields, keep others
                for field in [
                    "name",
                    "asset_type",
                    "owner",
                    "owner_email",
                    "department",
                    "status",
                    "location",
                    "purchase_date",
                    "warranty_expiry",
                    "serial_number",
                    "employee_code",
                    "configuration",
                    "tags",
                    "accessories",
                    "invoice",
                ]:
                    if field in payload and payload[field] is not None:
                        item[field] = str(payload[field]).strip()
                item["updated_at"] = datetime.utcnow().isoformat()
                data[idx] = item
                
                # Check for assignment change
                # Logic: If it's a laptop, and owner changed (or was empty), and we have an email
                if item.get("asset_type", "").lower() == "laptop" and \
                   item.get("owner") and item.get("owner_email") and \
                   (item.get("owner") != original_owner):
                    self.email_notifier.send_assignment_email(item["owner_email"], item)
                    
                updated = item
                break
        if updated is not None:
            self._write_all(data)
        return updated

    def delete_asset(self, asset_id: str) -> bool:
        """Delete an asset by id."""
        data = self._read_all()
        new_data = [item for item in data if item.get("id") != asset_id]
        if len(new_data) == len(data):
            return False
        self._write_all(new_data)
        return True

