"""Sidebar navigation component."""
from typing import Callable

import customtkinter as ctk

from app.gui.theme import Colors, Theme


class Sidebar(ctk.CTkFrame):
    """Left sidebar with navigation buttons."""

    NAV_ITEMS = [
        ("Dashboard", "dashboard"),
        ("Importar datos", "import"),
        ("Mis archivos", "files"),
        ("Explorador", "data"),
        ("Limpieza", "clean"),
        ("Transformacion", "transform"),
        ("Estadisticas", "stats"),
        ("Visualizaciones", "charts"),
        ("Comparacion", "compare"),
        ("Herramientas", "tools"),
        ("Exportar", "export"),
        ("Proyectos", "projects"),
        ("Papelera", "trash"),
        ("Historial", "history"),
        ("Configuracion", "settings"),
        ("Ayuda", "help"),
    ]

    def __init__(self, parent, on_navigate: Callable[[str], None]):
        super().__init__(parent, fg_color=Colors.BG_SIDEBAR, corner_radius=0, width=220)
        self.on_navigate = on_navigate
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._active_view: str | None = None
        self.pack_propagate(False)
        self._build_ui()

    def _build_ui(self):
        from app.core.settings_manager import SettingsManager
        from app.core.branding_manager import BrandingManager
        
        settings = SettingsManager()
        branding = BrandingManager(settings)
        brand_data = branding.get_branding()
        
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(24, 8))

        logo_img = branding.get_logo_image(size=(32, 32))
        if logo_img:
            ctk.CTkLabel(
                logo_frame,
                text="",
                image=logo_img,
            ).pack(side="left", padx=(0, 10))

        text_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            text_frame,
            text=brand_data.get("app_name", "Data Analyzer"),
            font=Theme.heading(15),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            text_frame,
            text=brand_data.get("app_subtitle", "Pro Edition"),
            font=Theme.small(10),
            text_color=Colors.ACCENT,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkFrame(self, fg_color=Colors.BORDER, height=1).pack(fill="x", padx=16, pady=(16, 12))
        ctk.CTkLabel(
            self,
            text="NAVEGACION",
            font=Theme.small(10),
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=24, pady=(4, 8))

        for label, view_name in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                self,
                text=f"  {label}",
                font=Theme.body(13),
                fg_color="transparent",
                hover_color=Colors.BG_CARD_HOVER,
                text_color=Colors.TEXT_SECONDARY,
                anchor="w",
                height=36,
                corner_radius=8,
                command=lambda v=view_name: self._on_click(v),
            )
            btn.pack(fill="x", padx=12, pady=1)
            self._buttons[view_name] = btn

        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)
        ctk.CTkFrame(self, fg_color=Colors.BORDER, height=1).pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkLabel(self, text="v1.0.0", font=Theme.small(10), text_color=Colors.TEXT_MUTED).pack(pady=(0, 16))

    def _on_click(self, view_name: str):
        self.set_active(view_name)
        self.on_navigate(view_name)

    def set_active(self, view_name: str):
        self._active_view = view_name
        for name, btn in self._buttons.items():
            if name == view_name:
                btn.configure(
                    fg_color=Colors.ACCENT,
                    text_color="#FFFFFF",
                    hover_color=Colors.ACCENT_HOVER,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=Colors.TEXT_SECONDARY,
                    hover_color=Colors.BG_CARD_HOVER,
                )
