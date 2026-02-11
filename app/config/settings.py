import json
import os
from pathlib import Path
from .defaults import DEFAULT_SETTINGS

CONFIG_FILE = Path("config.json")

class SettingsManager:
    def __init__(self):
        self._settings = self.load_settings()

    def load_settings(self):
        if not CONFIG_FILE.exists():
            return DEFAULT_SETTINGS.copy()

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Merge with defaults to ensure all keys exist
                settings = DEFAULT_SETTINGS.copy()
                settings.update(data)
                return settings
        except Exception as e:
            print(f"Error loading settings: {e}")
            return DEFAULT_SETTINGS.copy()

    def save_settings(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        self._settings[key] = value
        self.save_settings()

# Global instance
settings = SettingsManager()
