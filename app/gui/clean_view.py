"""Data cleaning view."""
import customtkinter as ctk
from tkinter import messagebox
from app.core.data_manager import DataManager
from app.core.cleaner import DataCleaner
from app.gui.theme import Theme

class CleanView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.cleaner = DataCleaner(data_manager)
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Limpieza de Datos", "🧹").pack(anchor="w", padx=30, pady=(30, 20))
        
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=30)
        
        Theme.create_primary_button(actions, "Eliminar Duplicados", command=self._remove_duplicates).pack(side="left", padx=5)
        Theme.create_primary_button(actions, "Eliminar Filas Nulas", command=self._drop_na).pack(side="left", padx=5)
        Theme.create_secondary_button(actions, "Deshacer", command=self._undo).pack(side="right", padx=5)
        
        self.status = Theme.create_label(self, "Operaciones listas", style="secondary")
        self.status.pack(anchor="w", padx=30, pady=20)
        
    def _remove_duplicates(self):
        if not self.dm.has_data(): return
        res = self.cleaner.remove_duplicates()
        self.status.configure(text=f"Duplicados eliminados: {res['removed']}. Quedan: {res['remaining']}")
        
    def _drop_na(self):
        if not self.dm.has_data(): return
        res = self.cleaner.drop_missing_rows()
        self.status.configure(text=f"Filas eliminadas: {res['dropped']}. Quedan: {res['remaining']}")
        
    def _undo(self):
        if self.dm.undo():
            self.status.configure(text="Operación deshecha.")
        else:
            self.status.configure(text="No hay operaciones para deshacer.")
