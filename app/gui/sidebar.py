"""Sidebar navigation component."""
import customtkinter as ctk
from typing import Callable
from app.gui.theme import Colors, Theme


class Sidebar(ctk.CTkFrame):
    """Left sidebar with navigation buttons."""

    NAV_ITEMS = [
        ("📂", "Importar", "import"),
        ("📊", "Datos", "data"),
        ("🧹", "Limpiar", "clean"),
        ("📈", "Estadísticas", "stats"),
        ("❓", "Faltantes", "missing"),
        ("📉", "Gráficos", "charts"),
        ("💾", "Exportar", "export"),
    ]

    def __init__(self, parent, on_navigate: Callable[[str], None]):
        super().__init__(parent, fg_color=Colors.BG_SIDEBAR, corner_radius=0, width=220)
        self.on_navigate = on_navigate
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._active_view: str | None = None
        self.pack_propagate(False)
        self._build_ui()

    def _build_ui(self):
        # ── Logo area ──
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(24, 8))

        ctk.CTkLabel(
            logo_frame, text="📊", font=(Theme.FONT_FAMILY, 28),
        ).pack(side="left", padx=(4, 8))

        title_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="x")

        ctk.CTkLabel(
            title_frame, text="Data Analyzer",
            font=Theme.heading(16), text_color=Colors.TEXT_PRIMARY, anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame, text="Pro Edition",
            font=Theme.small(10), text_color=Colors.ACCENT, anchor="w",
        ).pack(anchor="w")

        # ── Divider ──
        ctk.CTkFrame(self, fg_color=Colors.BORDER, height=1).pack(
            fill="x", padx=16, pady=(16, 12),
        )

        # ── Section label ──
        ctk.CTkLabel(
            self, text="NAVEGACIÓN",
            font=Theme.small(10), text_color=Colors.TEXT_MUTED, anchor="w",
        ).pack(fill="x", padx=24, pady=(4, 8))

        # ── Navigation buttons ──
        for icon, label, view_name in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                self,
                text=f"  {icon}   {label}",
                font=Theme.body(13),
                fg_color="transparent",
                hover_color=Colors.BG_CARD_HOVER,
                text_color=Colors.TEXT_SECONDARY,
                anchor="w",
                height=40,
                corner_radius=8,
                command=lambda v=view_name: self._on_click(v),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self._buttons[view_name] = btn

        # ── Spacer ──
        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)

        # ── Bottom ──
        ctk.CTkFrame(self, fg_color=Colors.BORDER, height=1).pack(
            fill="x", padx=16, pady=(0, 8),
        )

        ctk.CTkLabel(
            self, text="v1.0.0",
            font=Theme.small(10), text_color=Colors.TEXT_MUTED,
        ).pack(pady=(0, 16))

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
