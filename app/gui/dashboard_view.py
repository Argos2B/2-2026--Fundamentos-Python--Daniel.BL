"""Dashboard overview for Data Analyzer Pro."""
import customtkinter as ctk

from app.core.data_manager import DataManager
from app.gui.theme import Colors, Theme


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager, on_navigate=None):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.on_navigate = on_navigate
        self.metric_cards = []
        self.recent_text = None
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Dashboard", "").pack(anchor="w", padx=28, pady=(28, 20))

        metrics = ctk.CTkFrame(self, fg_color="transparent")
        metrics.pack(fill="x", padx=28, pady=(0, 18))
        self.metric_cards = [
            Theme.create_metric_card(metrics, "Datasets", "0", "en sesion", Colors.ACCENT),
            Theme.create_metric_card(metrics, "Filas procesadas", "0", "dataset actual", Colors.ACCENT_SECONDARY),
            Theme.create_metric_card(metrics, "Analisis", "0", "sesiones", Colors.SUCCESS),
            Theme.create_metric_card(metrics, "Graficos", "0", "creados", Colors.WARNING),
        ]
        for i, card in enumerate(self.metric_cards):
            card.grid(row=0, column=i, sticky="nsew", padx=8, pady=4)
            metrics.grid_columnconfigure(i, weight=1)

        actions = Theme.create_card(self)
        actions.pack(fill="x", padx=28, pady=(0, 12))
        inner = ctk.CTkFrame(actions, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=18)
        ctk.CTkLabel(inner, text="Acciones rapidas", font=Theme.heading(18), text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(12, 0))
        Theme.create_primary_button(row, "Importar datos", command=lambda: self._go("import"), width=170).pack(side="left", padx=(0, 10))
        Theme.create_secondary_button(row, "Nuevo analisis", command=self._new_analysis, width=170).pack(side="left", padx=(0, 10))
        Theme.create_secondary_button(row, "Abrir proyecto", command=lambda: self._go("projects"), width=170).pack(side="left")

        recent = Theme.create_card(self)
        recent.pack(fill="both", expand=True, padx=28, pady=(0, 24))
        ctk.CTkLabel(recent, text="Actividad reciente", font=Theme.subheading(16), text_color=Colors.TEXT_PRIMARY, anchor="w").pack(anchor="w", padx=18, pady=(18, 8))
        self.recent_text = ctk.CTkTextbox(recent, height=220, font=Theme.mono(12))
        self.recent_text.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    def _go(self, view_name: str):
        if self.on_navigate:
            self.on_navigate(view_name)

    def _new_analysis(self):
        if not self.dm.has_data():
            self._go("import")
            return
        self.dm.new_analysis_session()
        self._go("stats")

    def refresh(self):
        rows = len(self.dm.df) if self.dm.has_data() else 0
        values = [len(self.dm.datasets), rows, len(self.dm.analysis_sessions), len(self.dm.created_charts)]
        for idx, value in enumerate(values):
            self._set_metric_text(idx, f"{value:,}")
        entries = self.dm.history.entries()[-12:]
        lines = [f"{entry.action or 'state'} - {entry.label} ({len(entry.dataframe):,} filas)" for entry in entries]
        if not lines:
            lines = ["Sin actividad. Importa un dataset para comenzar."]
        self.recent_text.configure(state="normal")
        self.recent_text.delete("1.0", "end")
        self.recent_text.insert("1.0", "\n".join(lines))
        self.recent_text.configure(state="disabled")

    def _set_metric_text(self, index: int, value: str):
        card = self.metric_cards[index]
        title_texts = {"Datasets", "Filas procesadas", "Analisis", "Graficos", "en sesion", "dataset actual", "sesiones", "creados"}
        for child in card.winfo_children():
            for nested in child.winfo_children() if hasattr(child, "winfo_children") else []:
                try:
                    current = nested.cget("text")
                except Exception:
                    continue
                if isinstance(current, str) and current not in title_texts:
                    nested.configure(text=str(value))
                    return
