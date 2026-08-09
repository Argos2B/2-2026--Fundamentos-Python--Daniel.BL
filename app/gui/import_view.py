"""Import data view."""
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from app.core.data_manager import DataManager
from app.gui.theme import Theme, Colors


class ImportView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager, on_imported=None):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.on_imported = on_imported
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Importar Datos", "📂").pack(anchor="w", padx=30, pady=(30, 20))
        
        card = Theme.create_card(self)
        card.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        
        Theme.create_label(inner, "Selecciona un archivo CSV para comenzar", style="heading").pack(pady=10)
        
        btn = Theme.create_primary_button(inner, "Seleccionar Archivo CSV", command=self._browse_file, width=250, height=50)
        btn.pack(pady=20)
        
        Theme.create_label(inner, "Soporta archivos .csv con distintos separadores y codificaciones", style="small").pack()

    def _browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
            try:
                self.dm.load_csv(path)
                messagebox.showinfo("Éxito", "Archivo importado correctamente")
                if self.on_imported:
                    self.on_imported()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")
