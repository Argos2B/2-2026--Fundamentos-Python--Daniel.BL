"""Data cleaning view with operational actions."""
import customtkinter as ctk
from tkinter import messagebox

from app.core.cleaner import DataCleaner
from app.core.data_manager import DataManager
from app.gui.theme import Theme


class CleanView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.cleaner = DataCleaner(data_manager)
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Limpieza de datos", "🧹").pack(anchor="w", padx=28, pady=(28, 18))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=28, pady=(0, 12))

        Theme.create_primary_button(actions, "Eliminar duplicados", command=self._remove_duplicates).pack(side="left", padx=(0, 8))
        Theme.create_primary_button(actions, "Eliminar filas nulas", command=self._drop_na).pack(side="left", padx=(0, 8))
        Theme.create_secondary_button(actions, "Normalizar texto", command=self._normalize_text).pack(side="left", padx=(0, 8))
        Theme.create_secondary_button(actions, "Deshacer", command=self._undo).pack(side="right")
        Theme.create_secondary_button(actions, "Rehacer", command=self._redo).pack(side="right", padx=(0, 8))

        self.status = Theme.create_label(self, "Operaciones listas", style="secondary")
        self.status.pack(anchor="w", padx=28, pady=(12, 8))

        self.summary = ctk.CTkTextbox(self, height=180, font=("Segoe UI", 12))
        self.summary.pack(fill="both", expand=True, padx=28, pady=(0, 24))
        self.summary.insert("1.0", "Selecciona una operación de limpieza para obtener una vista previa del impacto.")
        self.summary.configure(state="disabled")

    def _remove_duplicates(self):
        if not self.dm.has_data():
            messagebox.showwarning("Sin datos", "Carga un dataset antes de limpiar.")
            return
        result = self.cleaner.remove_duplicates()
        self.status.configure(text=f"Duplicados eliminados: {result['removed']}. Quedan: {result['remaining']}")
        self._set_summary(f"Duplicados eliminados: {result['removed']}\nRestantes: {result['remaining']}")

    def _drop_na(self):
        if not self.dm.has_data():
            messagebox.showwarning("Sin datos", "Carga un dataset antes de limpiar.")
            return
        result = self.cleaner.drop_missing_rows()
        self.status.configure(text=f"Filas eliminadas: {result['dropped']}. Quedan: {result['remaining']}")
        self._set_summary(f"Filas eliminadas: {result['dropped']}\nRestantes: {result['remaining']}")

    def _normalize_text(self):
        if not self.dm.has_data():
            messagebox.showwarning("Sin datos", "Carga un dataset antes de limpiar.")
            return
        if len(self.dm.df.columns) == 0:
            return
        column = str(self.dm.df.columns[0])
        result = self.cleaner.normalize_text(column, mode="strip")
        self.status.configure(text=f"Texto normalizado en '{column}'.")
        self._set_summary(f"Resultado: {result}")

    def _undo(self):
        if self.dm.undo():
            self.status.configure(text="Operación deshecha.")
        else:
            self.status.configure(text="No hay operaciones para deshacer.")

    def _redo(self):
        if self.dm.redo():
            self.status.configure(text="Operación rehacida.")
        else:
            self.status.configure(text="No hay operaciones para rehacer.")

    def _set_summary(self, text: str):
        self.summary.configure(state="normal")
        self.summary.delete("1.0", "end")
        self.summary.insert("1.0", text)
        self.summary.configure(state="disabled")
