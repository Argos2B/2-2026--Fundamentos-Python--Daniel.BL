"""Statistics view."""
import customtkinter as ctk
from app.core.data_manager import DataManager
from app.core.statistics import StatisticsEngine
from app.gui.theme import Theme

class StatsView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.stats = StatisticsEngine(data_manager)
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Estadísticas", "📈").pack(anchor="w", padx=30, pady=(30, 20))
        self.text_area = ctk.CTkTextbox(self, font=Theme.mono(12))
        self.text_area.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
    def refresh(self):
        if self.dm.has_data():
            desc = self.stats.descriptive_stats()
            self.text_area.configure(state="normal")
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", desc.to_string() if not desc.empty else "No hay columnas numéricas para analizar.")
            self.text_area.configure(state="disabled")
