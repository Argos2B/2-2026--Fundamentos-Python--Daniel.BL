"""Central settings persistence for the application."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SettingsManager:
    """Load, persist and restore app preferences."""

    DEFAULTS = {
        "language": "es",
        "theme": "dark",
        "confirmations": True,
        "show_recent_files": True,
        "show_statistics": True,
        "show_profile_panel": True,
        "show_recent_graphs": True,
        "show_dashboard_cards": True,
        "show_sidebar": True,
        "chart_legend": True,
        "chart_grid": True,
        "chart_labels": True,
        "chart_values": False,
        "chart_animations": True,
        "chart_default_format": "PNG",
        "chart_default_resolution": "High",
        "chart_export_background": "dark",
        "default_encoding": "utf-8",
        "default_delimiter": ",",
        "decimal_separator": ".",
        "auto_detect_types": True,
        "auto_detect_headers": True,
        "preview_rows": 50,
        "chunk_size": 10000,
        "confirm_before_delete": True,
        "max_memory_mb": 512,
        "enable_lazy_loading": True,
        "accounts_google_login": "pending",
        "default_data_folder": "",
        "project_folder": "",
        "export_folder": "",
        "workers": 2,
        "logging_level": "INFO",
        "ai_provider": "not_configured",
        "ai_api_key": "",
        "ai_model": "",
        "ai_allow_dataset_context": False,
        "ai_allow_data_samples": False,
        "google_client_id": "",
        "google_client_secret": "",
        "google_redirect_uri": "",
        "google_scopes": "openid email profile",
        "app_name": "Data Analyzer Pro",
        "logo_path": "",
        "icon_path": "",
        "favicon_path": "",
        "splash_path": "",
    }

    def __init__(self, storage_path: str | None = None):
        self.storage_path = Path(storage_path) if storage_path else Path(__file__).resolve().parents[1] / "settings.json"
        self._settings = self.DEFAULTS.copy()
        self.load()

    def load(self) -> dict[str, Any]:
        if not self.storage_path.exists():
            self._settings = self.DEFAULTS.copy()
            return self._settings
        try:
            with open(self.storage_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            self._settings = {**self.DEFAULTS, **data}
        except Exception:
            self._settings = self.DEFAULTS.copy()
        return self._settings

    def save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as handle:
            json.dump(self._settings, handle, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._settings[key] = value
        self.save()

    def reset(self) -> None:
        self._settings = self.DEFAULTS.copy()
        self.save()

    def all(self) -> dict[str, Any]:
        return self._settings.copy()
