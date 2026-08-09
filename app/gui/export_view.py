"""Export view."""
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from app.core.data_manager import DataManager
from app.core.exporter import DataExporter
from app.gui.theme import Theme

class ExportView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.exporter = DataExporter(data_manager)
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Exportar Datos", "💾").pack(anchor="w", padx=30, pady=(30, 20))
        
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=30)
        
        Theme.create_primary_button(actions, "Exportar a CSV", command=self._export_csv).pack(side="left", padx=10)
        Theme.create_primary_button(actions, "Exportar a Excel", command=self._export_excel).pack(side="left", padx=10)
        Theme.create_primary_button(actions, "Generar Reporte HTML", command=self._export_html).pack(side="left", padx=10)
        
    def _export_csv(self):
        if not self.dm.has_data(): return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            self.exporter.to_csv(path)
            messagebox.showinfo("Éxito", "Exportado a CSV")

    def _export_excel(self):
        if not self.dm.has_data(): return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if path:
            self.exporter.to_excel(path)
            messagebox.showinfo("Éxito", "Exportado a Excel")

    def _export_html(self):
        if not self.dm.has_data(): return
        path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML Report", "*.html")])
        if path:
            self.exporter.to_html_report(path)
            messagebox.showinfo("Éxito", "Reporte HTML generado")
