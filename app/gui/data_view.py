"""Data table view."""
import customtkinter as ctk
from app.core.data_manager import DataManager
from app.gui.theme import Theme

class DataView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Vista de Datos", "📊").pack(anchor="w", padx=30, pady=(30, 20))
        self.info_label = Theme.create_label(self, "Sin datos", style="secondary")
        self.info_label.pack(anchor="w", padx=30, pady=(0, 20))
        
        self.text_area = ctk.CTkTextbox(self, font=Theme.mono(12))
        self.text_area.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
    def refresh(self):
        if self.dm.has_data():
            self.info_label.configure(text=self.dm.get_shape_str())
            self.text_area.configure(state="normal")
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", self.dm.df.head(100).to_string())
            self.text_area.configure(state="disabled")
