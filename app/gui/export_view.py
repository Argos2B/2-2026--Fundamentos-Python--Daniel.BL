"""Export view."""
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

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
        Theme.create_section_title(self, "Exportar datos", "").pack(anchor="w", padx=30, pady=(30, 20))
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=30, pady=(0, 12))
        self.format_menu = Theme.create_dropdown(controls, ["csv", "tsv", "xlsx", "xlsm", "ods", "json", "jsonl", "xml", "yaml", "html", "html_report", "parquet", "feather"], width=180)
        self.format_menu.pack(side="left", padx=(0, 10))
        Theme.create_primary_button(controls, "Exportar", command=self._export, width=130).pack(side="left", padx=4)
        Theme.create_secondary_button(controls, "Reporte HTML", command=self._export_report, width=150).pack(side="left", padx=4)
        self.status = Theme.create_label(self, "Selecciona un formato para exportar el dataset actual.", "secondary")
        self.status.pack(anchor="w", padx=30, pady=(8, 0))

    def _export(self):
        if not self.dm.has_data():
            messagebox.showwarning("Exportar", "No hay datos para exportar.")
            return
        fmt = self.format_menu.get()
        ext = ".html" if fmt == "html_report" else f".{fmt}"
        path = filedialog.asksaveasfilename(defaultextension=ext)
        if not path:
            return
        try:
            if fmt == "csv":
                result = self.exporter.to_csv(path)
            elif fmt == "tsv":
                result = self.exporter.to_csv(path, separator="\t")
            elif fmt == "xlsx":
                result = self.exporter.to_excel(path)
            elif fmt == "json":
                result = self.exporter.to_json(path)
            elif fmt == "jsonl":
                result = self.exporter.to_json(path, lines=True)
            elif fmt == "html":
                result = self.exporter.to_html(path)
            elif fmt == "html_report":
                result = self.exporter.to_html_report(path)
            elif fmt == "parquet":
                result = self.exporter.to_parquet(path)
            elif fmt == "xml":
                result = self.exporter.to_xml(path)
            elif fmt == "yaml":
                result = self.exporter.to_yaml(path)
            elif fmt == "feather":
                result = self.exporter.to_feather(path)
            elif fmt in {"xlsm", "ods"}:
                result = self.exporter.to_excel(path)
            else:
                raise ValueError(f"Formato no soportado: {fmt}")
            if not result.get("success"):
                raise ValueError(result.get("error", "No se pudo exportar."))
        except Exception as exc:
            messagebox.showerror("Exportar", f"No se pudo exportar:\n{exc}")
            return
        self.status.configure(text=f"Exportado: {Path(result['path']).name}")
        messagebox.showinfo("Exportar", f"Archivo exportado:\n{result['path']}")

    def _export_report(self):
        self.format_menu.set("html_report")
        self._export()
