"""Purpose-built workflow views that replace duplicated dashboard screens."""
from __future__ import annotations

import os
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk
import pandas as pd

from app.core.auth_manager import AuthManager
from app.core.ai_manager import AIManager
from app.core.cleaner import DataCleaner
from app.core.data_manager import DataManager
from app.core.exporter import DataExporter
from app.core.project_manager import ProjectManager
from app.core.shortcuts_manager import ShortcutConflictError, ShortcutsManager
from app.core.settings_manager import SettingsManager
from app.core.transformation_engine import TransformationEngine
from app.gui.theme import Colors, Theme


def _write_textbox(box: ctk.CTkTextbox, text: str) -> None:
    box.configure(state="normal")
    box.delete("1.0", "end")
    box.insert("1.0", text)
    box.configure(state="disabled")


class FilesView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager, on_open=None, on_analyze=None):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.on_open = on_open
        self.on_analyze = on_analyze
        self.exporter = DataExporter(data_manager)
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Mis archivos", "").pack(anchor="w", padx=28, pady=(28, 18))
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=28, pady=(0, 12))
        self.search = Theme.create_input(controls, "Buscar dataset", width=240)
        self.search.pack(side="left")
        self.search.bind("<KeyRelease>", lambda _event: self.refresh())
        self.dataset_menu = Theme.create_dropdown(controls, ["Sin datasets"], width=240)
        self.dataset_menu.pack(side="left", padx=10)
        Theme.create_primary_button(controls, "Abrir", self._open, width=90).pack(side="left", padx=4)
        Theme.create_secondary_button(controls, "Analizar", self._analyze, width=100).pack(side="left", padx=4)
        Theme.create_secondary_button(controls, "Renombrar", self._rename, width=110).pack(side="left", padx=4)
        Theme.create_secondary_button(controls, "Duplicar", self._duplicate, width=100).pack(side="left", padx=4)
        Theme.create_secondary_button(controls, "Exportar", self._export, width=100).pack(side="left", padx=4)
        Theme.create_danger_button(controls, "Eliminar", self._delete, width=100).pack(side="right")
        self.table = ctk.CTkTextbox(self, font=Theme.mono(12))
        self.table.pack(fill="both", expand=True, padx=28, pady=(0, 28))

    def _selected(self) -> str | None:
        value = self.dataset_menu.get()
        return value if value and value != "Sin datasets" else None

    def _open(self):
        name = self._selected()
        if name:
            self.dm.open_dataset(name)
            if self.on_open:
                self.on_open()

    def _analyze(self):
        name = self._selected()
        if name:
            self.dm.open_dataset(name)
            self.dm.new_analysis_session()
            if self.on_analyze:
                self.on_analyze()

    def _rename(self):
        name = self._selected()
        if not name:
            return
        new_name = simpledialog.askstring("Renombrar dataset", "Nuevo nombre:", initialvalue=name)
        if new_name:
            self.dm.rename_dataset(name, new_name)
            self.refresh()

    def _duplicate(self):
        name = self._selected()
        if name:
            self.dm.duplicate_dataset(name)
            self.refresh()

    def _delete(self):
        name = self._selected()
        if name and messagebox.askyesno("Eliminar dataset", f"Mover '{name}' a la papelera?"):
            self.dm.delete_dataset(name)
            self.refresh()

    def _export(self):
        name = self._selected()
        if not name:
            return
        self.dm.open_dataset(name)
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx"), ("JSON", "*.json")])
        if not path:
            return
        suffix = Path(path).suffix.lower()
        if suffix == ".xlsx":
            result = self.exporter.to_excel(path)
        elif suffix == ".json":
            result = self.exporter.to_json(path)
        else:
            result = self.exporter.to_csv(path)
        messagebox.showinfo("Exportacion", f"Archivo exportado: {result['path']}")

    def refresh(self):
        records = self.dm.list_datasets()
        query = self.search.get().strip().lower() if hasattr(self, "search") else ""
        if query:
            records = [record for record in records if query in record["name"].lower()]
        names = [record["name"] for record in records] or ["Sin datasets"]
        self.dataset_menu.configure(values=names)
        self.dataset_menu.set(names[0])
        lines = ["Nombre | Formato | Filas | Columnas | Tamano | Ubicacion"]
        for record in records:
            lines.append(
                f"{record['name']} | {record['format']} | {record['rows']:,} | {record['cols']} | "
                f"{record['memory_bytes'] / 1024:.1f} KB | {record['file_path'] or 'sesion'}"
            )
        if len(lines) == 1:
            lines.append("No hay datasets cargados. Importa datos para llenar este administrador.")
        _write_textbox(self.table, "\n".join(lines))


class TransformView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.engine = TransformationEngine(data_manager)
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Transformacion", "").pack(anchor="w", padx=28, pady=(28, 18))
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=28, pady=(0, 12))
        self.column_menu = Theme.create_dropdown(grid, ["Sin columnas"], width=190)
        self.column_menu.grid(row=0, column=0, padx=4, pady=4)
        self.condition_menu = Theme.create_dropdown(grid, ["==", "!=", ">", ">=", "<", "<=", "contains"], width=120)
        self.condition_menu.grid(row=0, column=1, padx=4, pady=4)
        self.value_entry = Theme.create_input(grid, "Valor", width=160)
        self.value_entry.grid(row=0, column=2, padx=4, pady=4)
        Theme.create_primary_button(grid, "Filtrar", self._filter, width=100).grid(row=0, column=3, padx=4)
        Theme.create_secondary_button(grid, "Ordenar ASC", lambda: self._sort(True), width=120).grid(row=0, column=4, padx=4)
        Theme.create_secondary_button(grid, "Ordenar DESC", lambda: self._sort(False), width=130).grid(row=0, column=5, padx=4)

        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=28, pady=(0, 12))
        self.rename_entry = Theme.create_input(row2, "Nuevo nombre de columna", width=220)
        self.rename_entry.pack(side="left", padx=4)
        Theme.create_secondary_button(row2, "Renombrar", self._rename, width=110).pack(side="left", padx=4)
        Theme.create_danger_button(row2, "Eliminar columna", self._drop_column, width=140).pack(side="left", padx=4)
        self.expr_name = Theme.create_input(row2, "Nueva columna", width=150)
        self.expr_name.pack(side="left", padx=4)
        self.expr = Theme.create_input(row2, "Expresion pandas eval", width=220)
        self.expr.pack(side="left", padx=4)
        Theme.create_primary_button(row2, "Crear", self._create_column, width=90).pack(side="left", padx=4)

        self.preview = ctk.CTkTextbox(self, font=Theme.mono(12))
        self.preview.pack(fill="both", expand=True, padx=28, pady=(0, 28))

    def _value(self):
        raw = self.value_entry.get()
        try:
            return float(raw)
        except ValueError:
            return raw

    def _apply(self, df: pd.DataFrame, action: str):
        self.dm.apply_dataframe(df, action)
        self.refresh()

    def _filter(self):
        self._apply(self.engine.filter_rows(self.column_menu.get(), self.condition_menu.get(), self._value()), "Filtro aplicado")

    def _sort(self, ascending: bool):
        self._apply(self.engine.sort_values(self.column_menu.get(), ascending), "Orden aplicado")

    def _rename(self):
        new_name = self.rename_entry.get().strip()
        if new_name:
            self._apply(self.engine.rename_columns({self.column_menu.get(): new_name}), "Columna renombrada")

    def _drop_column(self):
        column = self.column_menu.get()
        if column and messagebox.askyesno("Eliminar columna", f"Eliminar columna '{column}'?"):
            self._apply(self.engine.drop_columns([column]), "Columna eliminada")

    def _create_column(self):
        name = self.expr_name.get().strip()
        expr = self.expr.get().strip()
        if name and expr:
            self._apply(self.engine.add_calculated_column(name, expr), "Columna calculada")

    def refresh(self):
        if not self.dm.has_data():
            self.column_menu.configure(values=["Sin columnas"])
            self.column_menu.set("Sin columnas")
            _write_textbox(self.preview, "Carga un dataset para transformar datos.")
            return
        columns = [str(col) for col in self.dm.df.columns]
        self.column_menu.configure(values=columns)
        if self.column_menu.get() not in columns:
            self.column_menu.set(columns[0])
        _write_textbox(self.preview, self.dm.df.head(30).to_string(index=False))


class CompareView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Comparacion", "").pack(anchor="w", padx=28, pady=(28, 18))
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=28, pady=(0, 12))
        self.a_menu = Theme.create_dropdown(controls, ["Dataset A"], width=220)
        self.a_menu.pack(side="left", padx=4)
        self.b_menu = Theme.create_dropdown(controls, ["Dataset B"], width=220)
        self.b_menu.pack(side="left", padx=4)
        Theme.create_primary_button(controls, "Comparar", self._compare, width=120).pack(side="left", padx=8)
        self.output = ctk.CTkTextbox(self, font=Theme.mono(12))
        self.output.pack(fill="both", expand=True, padx=28, pady=(0, 28))

    def _compare(self):
        a_name, b_name = self.a_menu.get(), self.b_menu.get()
        if a_name not in self.dm.datasets or b_name not in self.dm.datasets:
            return
        a = self.dm.datasets[a_name].dataframe
        b = self.dm.datasets[b_name].dataframe
        common = [col for col in a.columns if col in b.columns]
        only_a = [col for col in a.columns if col not in b.columns]
        only_b = [col for col in b.columns if col not in a.columns]
        same_rows = 0
        if common:
            same_rows = len(a[common].merge(b[common].drop_duplicates(), how="inner"))
        text = [
            f"Dataset A: {a_name} - {len(a):,} filas x {len(a.columns)} columnas",
            f"Dataset B: {b_name} - {len(b):,} filas x {len(b.columns)} columnas",
            "",
            f"Columnas comunes: {len(common)}",
            f"Solo en A: {only_a}",
            f"Solo en B: {only_b}",
            f"Diferencia de filas: {len(b) - len(a):,}",
            f"Filas coincidentes por columnas comunes: {same_rows:,}",
            "",
            "Tipos diferentes:",
        ]
        for col in common:
            if str(a[col].dtype) != str(b[col].dtype):
                text.append(f"- {col}: {a[col].dtype} vs {b[col].dtype}")
        _write_textbox(self.output, "\n".join(text))

    def refresh(self):
        names = list(self.dm.datasets.keys()) or ["Sin datasets"]
        self.a_menu.configure(values=names)
        self.b_menu.configure(values=names)
        self.a_menu.set(names[0])
        self.b_menu.set(names[1] if len(names) > 1 else names[0])


class ToolsView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.cleaner = DataCleaner(data_manager)
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Herramientas", "").pack(anchor="w", padx=28, pady=(28, 18))
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=28, pady=(0, 12))
        self.column_menu = Theme.create_dropdown(controls, ["Sin columnas"], width=210)
        self.column_menu.pack(side="left", padx=4)
        Theme.create_primary_button(controls, "Detectar outliers IQR", self._outliers, width=170).pack(side="left", padx=4)
        Theme.create_secondary_button(controls, "Validar emails", self._validate_email, width=140).pack(side="left", padx=4)
        Theme.create_secondary_button(controls, "Convertir a numero", self._convert_numeric, width=160).pack(side="left", padx=4)
        self.output = ctk.CTkTextbox(self, font=Theme.mono(12))
        self.output.pack(fill="both", expand=True, padx=28, pady=(0, 28))

    def _outliers(self):
        col = self.column_menu.get()
        if not self.dm.has_data() or col not in self.dm.df:
            return
        series = pd.to_numeric(self.dm.df[col], errors="coerce").dropna()
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        outliers = series[(series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)]
        _write_textbox(self.output, f"Outliers IQR en {col}: {len(outliers)}\n\n{outliers.head(50).to_string()}")

    def _validate_email(self):
        col = self.column_menu.get()
        if not self.dm.has_data() or col not in self.dm.df:
            return
        valid = self.dm.df[col].astype(str).str.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", na=False)
        _write_textbox(self.output, f"Emails validos: {int(valid.sum())}\nInvalidos: {int((~valid).sum())}")

    def _convert_numeric(self):
        col = self.column_menu.get()
        if self.dm.has_data() and col in self.dm.df:
            result = self.cleaner.convert_type(col, "numeric")
            _write_textbox(self.output, str(result))

    def refresh(self):
        columns = [str(col) for col in self.dm.df.columns] if self.dm.has_data() else ["Sin columnas"]
        self.column_menu.configure(values=columns)
        self.column_menu.set(columns[0])


class HistoryView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Historial", "").pack(anchor="w", padx=28, pady=(28, 18))
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=28, pady=(0, 12))
        Theme.create_secondary_button(controls, "Deshacer", self._undo, width=110).pack(side="left", padx=4)
        Theme.create_secondary_button(controls, "Rehacer", self._redo, width=110).pack(side="left", padx=4)
        Theme.create_danger_button(controls, "Eliminar historial", self._clear, width=150).pack(side="right")
        self.output = ctk.CTkTextbox(self, font=Theme.mono(12))
        self.output.pack(fill="both", expand=True, padx=28, pady=(0, 28))

    def _undo(self):
        self.dm.undo()
        self.refresh()

    def _redo(self):
        self.dm.redo()
        self.refresh()

    def _clear(self):
        if messagebox.askyesno("Historial", "Eliminar historial de undo/redo?"):
            self.dm.history.clear()
            self.refresh()

    def refresh(self):
        entries = self.dm.history.entries()
        lines = ["Operacion | Dataset | Filas | Columnas"]
        for entry in entries:
            lines.append(f"{entry.action or 'state'} | {entry.label} | {len(entry.dataframe):,} | {len(entry.dataframe.columns)}")
        if len(lines) == 1:
            lines.append("Sin operaciones registradas.")
        _write_textbox(self.output, "\n".join(lines))


class TrashView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Papelera", "").pack(anchor="w", padx=28, pady=(28, 18))
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=28, pady=(0, 12))
        self.trash_menu = Theme.create_dropdown(controls, ["Papelera vacia"], width=300)
        self.trash_menu.pack(side="left", padx=4)
        Theme.create_primary_button(controls, "Restaurar", self._restore, width=120).pack(side="left", padx=4)
        Theme.create_danger_button(controls, "Eliminar permanentemente", self._delete_permanently, width=210).pack(side="left", padx=4)
        Theme.create_danger_button(controls, "Vaciar papelera", self._empty, width=150).pack(side="right", padx=4)
        self.output = ctk.CTkTextbox(self, font=Theme.mono(12))
        self.output.pack(fill="both", expand=True, padx=28, pady=(0, 28))
        self.refresh()

    def _selected_id(self) -> str | None:
        value = self.trash_menu.get()
        if not value or value == "Papelera vacia":
            return None
        return value.split(" | ", 1)[0]

    def _restore(self):
        item_id = self._selected_id()
        if not item_id:
            return
        try:
            restored = self.dm.restore_from_trash(item_id)
            messagebox.showinfo("Papelera", f"Restaurado: {restored}")
        except Exception as exc:
            messagebox.showerror("Papelera", str(exc))
        self.refresh()

    def _delete_permanently(self):
        item_id = self._selected_id()
        if item_id and messagebox.askyesno("Eliminar permanentemente", "Esta accion no se puede deshacer. Continuar?"):
            self.dm.delete_trash_item_permanently(item_id)
            self.refresh()

    def _empty(self):
        if messagebox.askyesno("Vaciar papelera", "Eliminar permanentemente todos los elementos?"):
            removed = self.dm.empty_trash()
            messagebox.showinfo("Papelera", f"Elementos eliminados: {removed}")
            self.refresh()

    def refresh(self):
        items = self.dm.list_trash()
        labels = [f"{item['id']} | {item['item_type']} | {item['name']}" for item in items] or ["Papelera vacia"]
        self.trash_menu.configure(values=labels)
        self.trash_menu.set(labels[0])
        lines = ["ID | Tipo | Nombre | Eliminado | Ubicacion original"]
        for item in items:
            lines.append(f"{item['id']} | {item['item_type']} | {item['name']} | {item['deleted_at']} | {item['original_location']}")
        if len(lines) == 1:
            lines.append("No hay elementos en la papelera.")
        _write_textbox(self.output, "\n".join(lines))


class SettingsView(ctk.CTkFrame):
    SECTIONS = ["General", "Apariencia", "Datos", "Graficos", "Rendimiento", "Cuenta", "Privacidad", "Atajos", "IA", "Carpetas", "Avanzado"]

    def __init__(self, parent, data_manager: DataManager, on_theme_change=None):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.settings = SettingsManager()
        self.auth = AuthManager(self.settings)
        self.shortcuts = ShortcutsManager()
        self.ai = AIManager(self.settings)
        self.on_theme_change = on_theme_change
        self.content = None
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Configuracion", "").pack(anchor="w", padx=28, pady=(28, 18))
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=(0, 28))
        side = ctk.CTkFrame(body, fg_color=Colors.BG_CARD, width=180, corner_radius=8)
        side.pack(side="left", fill="y", padx=(0, 12))
        side.pack_propagate(False)
        for section in self.SECTIONS:
            Theme.create_secondary_button(side, section, lambda s=section: self._show(s), width=150).pack(fill="x", padx=12, pady=5)
        self.content = ctk.CTkFrame(body, fg_color=Colors.BG_CARD, corner_radius=8)
        self.content.pack(side="left", fill="both", expand=True)
        self._show("General")

    def _clear(self):
        for child in self.content.winfo_children():
            child.destroy()

    def _switch(self, key: str, text: str):
        var = ctk.BooleanVar(value=bool(self.settings.get(key)))
        ctk.CTkCheckBox(
            self.content,
            text=text,
            variable=var,
            command=lambda: self.settings.set(key, var.get()),
            text_color=Colors.TEXT_PRIMARY,
        ).pack(anchor="w", padx=18, pady=6)

    def _folder(self, key: str, text: str):
        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=6)
        Theme.create_label(row, text, "secondary").pack(side="left")
        Theme.create_secondary_button(row, "Seleccionar", lambda: self._choose_folder(key), width=120).pack(side="right")

    def _choose_folder(self, key: str):
        folder = filedialog.askdirectory(title="Seleccionar carpeta")
        if folder:
            self.settings.set(key, folder)
            self._show("General")

    def _show(self, section: str):
        self._clear()
        Theme.create_label(self.content, section, "heading").pack(anchor="w", padx=18, pady=(18, 12))
        if section == "General":
            for key, text in [
                ("open_last_project", "Abrir ultimo proyecto"),
                ("restore_session", "Restaurar sesion"),
                ("show_recent_files", "Mostrar archivos recientes"),
                ("confirm_before_delete", "Confirmar eliminacion"),
                ("confirm_overwrite", "Confirmar sobrescritura"),
                ("confirm_destructive", "Confirmar operaciones destructivas"),
            ]:
                self._switch(key, text)
            self._folder("default_data_folder", "Carpeta predeterminada")
            self._folder("project_folder", "Carpeta de proyectos")
            self._folder("export_folder", "Carpeta de exportaciones")
        elif section == "Apariencia":
            menu = Theme.create_dropdown(self.content, ["dark", "light", "system"], self._set_theme, width=180)
            menu.set(self.settings.get("theme", "dark"))
            menu.pack(anchor="w", padx=18, pady=8)
            for key, text in [
                ("show_statistics", "Mostrar estadisticas"),
                ("show_recent_files", "Mostrar archivos recientes"),
                ("show_recent_graphs", "Mostrar graficos recientes"),
                ("show_suggestions", "Mostrar sugerencias"),
                ("show_sidebar", "Mostrar barra lateral"),
                ("animations", "Animaciones"),
            ]:
                self._switch(key, text)
        elif section == "Datos":
            for key in ["default_encoding", "default_delimiter", "decimal_separator", "preview_rows", "chunk_size"]:
                self._entry_setting(key)
            self._switch("auto_detect_headers", "Detectar encabezados")
            self._switch("auto_detect_types", "Detectar tipos")
            self._switch("enable_lazy_loading", "Lazy loading")
        elif section == "Graficos":
            for key, text in [
                ("chart_legend", "Leyenda"),
                ("chart_grid", "Cuadricula"),
                ("chart_labels", "Etiquetas"),
                ("chart_values", "Valores"),
                ("chart_animations", "Animaciones"),
            ]:
                self._switch(key, text)
            self._entry_setting("chart_default_format")
            self._entry_setting("chart_default_resolution")
        elif section == "Rendimiento":
            for key in ["workers", "chunk_size", "max_memory_mb"]:
                self._entry_setting(key)
            self._switch("enable_cache", "Cache")
            self._switch("enable_lazy_loading", "Lazy loading")
        elif section == "Cuenta":
            status = self.auth.get_status()
            user = status.get("user") or {}
            account_text = "No has iniciado sesion." if not user else f"{user.get('name', '')}\n{user.get('email', '')}\nPlan actual: Local"
            Theme.create_label(self.content, account_text, "secondary").pack(anchor="w", padx=18, pady=8)
            Theme.create_label(self.content, status["message"], "small").pack(anchor="w", padx=18, pady=8)
            Theme.create_primary_button(self.content, "Continuar con Google", self._oauth, width=180).pack(anchor="w", padx=18, pady=8)
            Theme.create_secondary_button(self.content, "Cerrar sesion", self._logout, width=150).pack(anchor="w", padx=18, pady=8)
            self._entry_setting("google_client_id")
            self._entry_setting("google_redirect_uri")
            self._entry_setting("google_scopes")
        elif section == "Privacidad":
            Theme.create_danger_button(self.content, "Eliminar historial", self._clear_history, width=180).pack(anchor="w", padx=18, pady=8)
            Theme.create_secondary_button(self.content, "Exportar configuracion", self._export_settings, width=190).pack(anchor="w", padx=18, pady=8)
            Theme.create_secondary_button(self.content, "Importar configuracion", self._import_settings, width=190).pack(anchor="w", padx=18, pady=8)
            Theme.create_danger_button(self.content, "Restablecer preferencias", self._reset_settings, width=210).pack(anchor="w", padx=18, pady=8)
        elif section == "Atajos":
            labels = {
                "open": "Abrir",
                "import": "Importar",
                "save": "Guardar",
                "export": "Exportar",
                "undo": "Deshacer",
                "redo": "Rehacer",
                "search": "Buscar",
                "new_analysis": "Nuevo analisis",
                "open_project": "Abrir proyecto",
            }
            for action, label in labels.items():
                row = ctk.CTkFrame(self.content, fg_color="transparent")
                row.pack(fill="x", padx=18, pady=5)
                Theme.create_label(row, label, "secondary").pack(side="left")
                entry = Theme.create_input(row, "", width=170)
                entry.insert(0, self.shortcuts.get(action))
                entry.pack(side="left", padx=12)
                Theme.create_secondary_button(row, "Cambiar", lambda a=action, e=entry: self._set_shortcut(a, e.get()), width=90).pack(side="left", padx=4)
                Theme.create_secondary_button(row, "Restablecer", lambda a=action: self._reset_shortcut(a), width=110).pack(side="left", padx=4)
            Theme.create_danger_button(self.content, "Restaurar todos", self._reset_all_shortcuts, width=150).pack(anchor="w", padx=18, pady=12)
        elif section == "IA":
            provider = Theme.create_dropdown(self.content, ["not_configured", "openai", "gemini", "anthropic", "custom"], lambda v: self.settings.set("ai_provider", v), width=180)
            provider.set(self.settings.get("ai_provider", "not_configured"))
            provider.pack(anchor="w", padx=18, pady=8)
            self._entry_setting("ai_model")
            self._entry_setting("ai_api_key")
            self._switch("ai_allow_dataset_context", "Permitir contexto del dataset")
            self._switch("ai_allow_data_samples", "Permitir enviar muestras de datos")
            Theme.create_label(self.content, self.ai.ask("estado", self.dm).message, "small").pack(anchor="w", padx=18, pady=8)
        elif section == "Carpetas":
            self._folder("default_data_folder", "Carpeta predeterminada")
            self._folder("project_folder", "Carpeta de proyectos")
            self._folder("export_folder", "Carpeta de exportaciones")
        elif section == "Avanzado":
            self._entry_setting("logging_level")
            Theme.create_label(self.content, f"Carpeta de datos: {Path.cwd()}", "secondary").pack(anchor="w", padx=18, pady=8)
            Theme.create_secondary_button(self.content, "Diagnostico", self._diagnostics, width=130).pack(anchor="w", padx=18, pady=8)

    def _entry_setting(self, key: str):
        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=5)
        Theme.create_label(row, key, "secondary").pack(side="left")
        entry = Theme.create_input(row, "", width=180)
        entry.insert(0, str(self.settings.get(key, "")))
        entry.pack(side="right")
        entry.bind("<FocusOut>", lambda _event, e=entry, k=key: self.settings.set(k, e.get()))

    def _set_theme(self, value: str):
        self.settings.set("theme", value)
        ctk.set_appearance_mode(value)
        if self.on_theme_change:
            self.on_theme_change(value)

    def _set_shortcut(self, action: str, value: str):
        try:
            self.shortcuts.set(action, value)
            messagebox.showinfo("Atajos", "Atajo actualizado. Reinicia la aplicacion para re-vincularlo.")
        except ShortcutConflictError as exc:
            messagebox.showwarning("Atajo en uso", str(exc))
        except Exception as exc:
            messagebox.showerror("Atajos", str(exc))
        self._show("Atajos")

    def _reset_shortcut(self, action: str):
        self.shortcuts.reset(action)
        self._show("Atajos")

    def _reset_all_shortcuts(self):
        self.shortcuts.reset_all()
        self._show("Atajos")

    def _oauth(self):
        status = self.auth.start_oauth()
        auth_url = status.get("auth_url")
        if auth_url:
            import webbrowser
            import threading
            import time
            import json
            import urllib.request
            import urllib.error

            webbrowser.open(auth_url)
            messagebox.showinfo("Google OAuth", "Se ha abierto el navegador para continuar.\nInicia sesión en Google y espera unos segundos.")
            
            state = self.auth._oauth_state
            api_host = self.settings.get("api_host", "127.0.0.1")
            api_port = self.settings.get("api_port", 8000)
            base_url = f"http://{api_host}:{api_port}"

            def poll_auth():
                max_attempts = 60
                for _ in range(max_attempts):
                    try:
                        req = urllib.request.Request(f"{base_url}/auth/google/session?state={state}")
                        with urllib.request.urlopen(req) as response:
                            if response.status == 200:
                                data = json.loads(response.read().decode())
                                token = data.get("access_token")
                                if token:
                                    # Fetch user profile in background thread
                                    user_data = self._fetch_user_profile(base_url, token)
                                    if user_data:
                                        self.after(0, lambda ud=user_data: self._complete_oauth_success(ud))
                                    else:
                                        self.after(0, lambda: self._oauth_error("No se pudo obtener el perfil de usuario."))
                                    return
                    except urllib.error.HTTPError as e:
                        if e.code == 202:
                            pass
                        else:
                            self.after(0, lambda err=e: self._oauth_error(str(err)))
                            return
                    except Exception:
                        pass
                    time.sleep(1)
                self.after(0, lambda: self._oauth_error("Tiempo de espera agotado."))

            threading.Thread(target=poll_auth, daemon=True).start()
        else:
            messagebox.showwarning("Google OAuth", status["message"])

    def _fetch_user_profile(self, base_url: str, token: str) -> dict | None:
        """Fetch /users/me from the backend (called from background thread)."""
        import urllib.request
        import json
        try:
            req = urllib.request.Request(f"{base_url}/users/me")
            req.add_header("Authorization", f"Bearer {token}")
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except Exception:
            return None

    def _complete_oauth_success(self, user_data: dict):
        """Handle successful OAuth — called on main thread via self.after()."""
        try:
            self.auth.complete_login(user_data)
            self._show("Cuenta")
            messagebox.showinfo("Google OAuth", "Inicio de sesión completado con éxito.")
        except Exception as e:
            self._oauth_error(f"Error al obtener perfil: {e}")

    def _oauth_error(self, err):
        messagebox.showerror("Google OAuth Error", f"Fallo al autenticar:\n{err}")

    def _logout(self):
        self.auth.logout()
        self._show("Cuenta")

    def _clear_history(self):
        if messagebox.askyesno("Privacidad", "Eliminar historial local?"):
            self.dm.history.clear()

    def _export_settings(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            Path(path).write_text(self.settings.storage_path.read_text(encoding="utf-8"), encoding="utf-8")

    def _import_settings(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            self.settings.storage_path.write_text(Path(path).read_text(encoding="utf-8"), encoding="utf-8")
            self.settings.load()
            self._show("General")

    def _reset_settings(self):
        if messagebox.askyesno("Configuracion", "Restablecer solo preferencias?"):
            self.settings.reset()
            self._show("General")

    def _diagnostics(self):
        info = self.dm.get_info() if self.dm.has_data() else {}
        messagebox.showinfo("Diagnostico", f"Datasets: {len(self.dm.datasets)}\nDataset actual: {info.get('file_name', 'N/A')}")


class ProjectView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.settings = SettingsManager()
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Proyectos", "").pack(anchor="w", padx=28, pady=(28, 18))
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=28, pady=(0, 12))
        Theme.create_primary_button(controls, "Nuevo proyecto", self._new_project, width=150).pack(side="left", padx=4)
        Theme.create_secondary_button(controls, "Abrir proyecto", self._open_project, width=150).pack(side="left", padx=4)
        Theme.create_secondary_button(controls, "Guardar", self._save_project, width=110).pack(side="left", padx=4)
        Theme.create_secondary_button(controls, "Guardar como", self._save_as, width=130).pack(side="left", padx=4)
        self.output = ctk.CTkTextbox(self, font=Theme.mono(12))
        self.output.pack(fill="both", expand=True, padx=28, pady=(0, 28))

    def _new_project(self):
        folder = filedialog.askdirectory(title="Carpeta del nuevo proyecto")
        if folder:
            self.dm.current_project = str(ProjectManager.create_project(folder))
            self.refresh()

    def _open_project(self):
        folder = filedialog.askdirectory(title="Abrir proyecto")
        if folder:
            ProjectManager.load_project(folder, self.dm)
            self.refresh()

    def _save_project(self):
        if not self.dm.current_project:
            self._save_as()
            return
        ProjectManager.save_project(self.dm.current_project, self.dm, self.settings.all())
        self.refresh()

    def _save_as(self):
        folder = filedialog.askdirectory(title="Guardar proyecto como")
        if folder:
            self.dm.current_project = folder
            self._save_project()

    def refresh(self):
        text = [
            f"Proyecto actual: {self.dm.current_project or 'Sin proyecto'}",
            f"Dataset actual: {self.dm.file_name or 'Sin dataset'}",
            f"Datasets en sesion: {len(self.dm.datasets)}",
            f"Operaciones en historial: {len(self.dm.history.entries())}",
        ]
        _write_textbox(self.output, "\n".join(text))


class HelpView(ctk.CTkFrame):
    TOPICS = {
        "Primeros pasos": "Crea o abre un proyecto, importa un dataset y revisa el explorador antes de limpiar o transformar.",
        "Importacion": "Puedes importar archivos locales, carpetas, URL y portapapeles. La aplicacion detecta formato, encoding y separador cuando es posible.",
        "Analisis": "El analisis usa el dataset activo para estadisticas descriptivas, faltantes y correlaciones.",
        "Limpieza": "Las operaciones de limpieza registran historial para permitir deshacer.",
        "Transformacion": "Filtra, ordena, renombra, elimina columnas y crea columnas calculadas con pandas eval.",
        "Graficos": "Los graficos usan columnas numericas u OHLC detectado para candlestick; pueden guardarse y exportarse.",
        "Exportacion": "Exporta datos y reportes. Si falta una dependencia, el error indica el motivo.",
        "Proyectos": "Guardar proyecto conserva datasets, historial, configuracion, sesiones y graficos.",
        "Configuracion": "Ajusta apariencia, datos, graficos, carpetas, privacidad, atajos e IA.",
        "Cuenta": "Google Login requiere Client ID y Redirect URI; no se almacenan contrasenas.",
        "Atajos": "Los atajos se pueden cambiar en Configuracion > Atajos y se validan conflictos.",
        "Preguntas frecuentes": "Si un archivo no importa, revisa formato real, extension, encoding y dependencias opcionales.",
        "Diagnostico": "Usa Configuracion > Avanzado > Diagnostico para ver estado de datasets y sesion.",
        "Asistente IA": "El asistente esta desacoplado por proveedor y no envia contexto privado sin permiso.",
    }

    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.settings = SettingsManager()
        self.ai = AIManager(self.settings)
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Ayuda", "").pack(anchor="w", padx=28, pady=(28, 18))
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(0, 12))
        self.search_entry = Theme.create_input(top, "Buscar ayuda...", width=320)
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda _event: self._search())
        Theme.create_primary_button(top, "Buscar", self._search, width=100).pack(side="left")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=(0, 28))
        side = ctk.CTkFrame(body, fg_color=Colors.BG_CARD, width=190, corner_radius=8)
        side.pack(side="left", fill="y", padx=(0, 12))
        side.pack_propagate(False)
        for topic in self.TOPICS:
            Theme.create_secondary_button(side, topic, lambda t=topic: self._show_topic(t), width=160).pack(fill="x", padx=10, pady=4)
        self.output = ctk.CTkTextbox(body, font=Theme.mono(12))
        self.output.pack(side="left", fill="both", expand=True)

        assistant = ctk.CTkFrame(self, fg_color="transparent")
        assistant.pack(fill="x", padx=28, pady=(0, 20))
        self.ai_entry = Theme.create_input(assistant, "Escribe tu pregunta...", width=420)
        self.ai_entry.pack(side="left", padx=(0, 8))
        Theme.create_primary_button(assistant, "Asistente IA", self._ask_ai, width=140).pack(side="left")
        self._show_topic("Primeros pasos")

    def _show_topic(self, topic: str):
        _write_textbox(self.output, f"{topic}\n\n{self.TOPICS[topic]}")

    def _search(self):
        query = self.search_entry.get().strip().lower()
        if not query:
            self._show_topic("Primeros pasos")
            return
        results = [f"{topic}: {text}" for topic, text in self.TOPICS.items() if query in topic.lower() or query in text.lower()]
        if not results:
            results = ["No se encontraron resultados locales. Revisa el Diagnostico o formula la pregunta al Asistente IA."]
        _write_textbox(self.output, "\n\n".join(results))

    def _ask_ai(self):
        question = self.ai_entry.get().strip()
        if not question:
            return
        response = self.ai.ask(question, self.dm)
        _write_textbox(self.output, f"Asistente de Data Analyzer Pro\n\nPregunta:\n{question}\n\nRespuesta:\n{response.message}")
