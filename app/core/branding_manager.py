"""Central branding configuration."""
from __future__ import annotations

from pathlib import Path
from typing import Any


class BrandingManager:
    DEFAULTS = {
        "app_name": "Data Analyzer Pro",
        "app_subtitle": "Pro Edition",
        "logo_path": "",
        "icon_path": "",
        "favicon_path": "",
        "splash_path": "",
    }

    def __init__(self, settings: Any | None = None):
        self.settings = settings
        self._logo_image = None

    def get_branding(self) -> dict[str, str]:
        values = self.DEFAULTS.copy()
        if self.settings is not None:
            for key in values:
                values[key] = str(self.settings.get(key, values[key]) or "")
        return values

    def set_asset(self, key: str, path: str) -> None:
        if key not in self.DEFAULTS:
            raise KeyError(f"Activo de marca desconocido: {key}")
        if path and not Path(path).exists():
            raise FileNotFoundError(path)
        if self.settings is not None:
            self.settings.set(key, path)
        if key == "logo_path":
            self._logo_image = None

    def get_logo_image(self, size: tuple[int, int] = (32, 32)) -> Any | None:
        """Devuelve un CTkImage del logo, o None si no hay logo configurado."""
        if self._logo_image is not None:
            return self._logo_image
            
        branding = self.get_branding()
        logo_path = branding.get("logo_path")
        
        if logo_path and Path(logo_path).exists():
            try:
                from PIL import Image
                import customtkinter as ctk
                img = Image.open(logo_path)
                self._logo_image = ctk.CTkImage(light_image=img, dark_image=img, size=size)
                return self._logo_image
            except Exception:
                pass
                
        return None
