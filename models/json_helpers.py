# models/json_helpers.py
import json
import os
from typing import List, Dict, Any

def _load_data(file_path: str) -> List[Dict[str, Any]]:
    """Loads data from a JSON file. Creates the file with an empty list if it doesn't exist."""
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump([], f)
        return []
    if os.path.getsize(file_path) == 0:  # Check for empty file
        return []
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if not isinstance(data, list):
                print(f"Warning: Data in {file_path} is not a list. Re-initializing as empty list.")
                _save_data(file_path, []) # Attempt to fix the file
                return []
            return data
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from {file_path}. Returning empty list.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while loading {file_path}: {e}. Returning empty list.")
        return []

def _save_data(file_path: str, all_items_data: List[Dict[str, Any]]) -> None:
    """Saves data to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(all_items_data, f, indent=4)
    except Exception as e:
        print(f"An unexpected error occurred while saving to {file_path}: {e}")