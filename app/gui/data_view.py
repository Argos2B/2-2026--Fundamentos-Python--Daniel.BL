"""Data table view with dataset preview and summary."""
import customtkinter as ctk
from tkinter import messagebox

from app.core.data_manager import DataManager
from app.core.transformation_engine import TransformationEngine
from app.gui.theme import Colors, Theme


class DataView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.engine = TransformationEngine(data_manager)
        self.page_size = 25
        self.current_page = 0
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Explorador de datos", "📊").pack(anchor="w", padx=28, pady=(28, 18))

        info_bar = ctk.CTkFrame(self, fg_color="transparent")
        info_bar.pack(fill="x", padx=28, pady=(0, 12))

        self.info_label = Theme.create_label(info_bar, "Sin datos", style="secondary")
        self.info_label.pack(anchor="w")

        self.summary_box = Theme.create_card(self)
        self.summary_box.pack(fill="x", padx=28, pady=(0, 12))
        self.summary_inner = ctk.CTkFrame(self.summary_box, fg_color="transparent")
        self.summary_inner.pack(fill="x", padx=18, pady=14)

        self.stats_labels = []
        for title, key in [("Filas", "rows"), ("Columnas", "cols"), ("Nulos", "nulls"), ("Duplicados", "duplicates")]:
            frame = ctk.CTkFrame(self.summary_inner, fg_color="transparent")
            frame.grid(row=0, column=len(self.stats_labels), sticky="nsew", padx=6)
            self.summary_inner.grid_columnconfigure(len(self.stats_labels), weight=1)
            label = ctk.CTkLabel(frame, text=title, font=Theme.small(), text_color=Colors.TEXT_MUTED)
            label.pack(anchor="w")
            value = ctk.CTkLabel(frame, text="0", font=Theme.heading(18), text_color=Colors.TEXT_PRIMARY)
            value.pack(anchor="w", pady=(4, 0))
            self.stats_labels.append((key, value))

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=28, pady=(0, 12))
        self.search_entry = Theme.create_input(controls, placeholder="Buscar en el dataset", width=260)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda _event: self._refresh_preview())

        self.page_label = Theme.create_label(controls, "Página 1", style="small")
        self.page_label.pack(side="right", padx=(0, 12))

        self.prev_btn = Theme.create_secondary_button(controls, "Anterior", command=self._previous_page, width=110)
        self.prev_btn.pack(side="right", padx=(0, 8))
        self.next_btn = Theme.create_secondary_button(controls, "Siguiente", command=self._next_page, width=110)
        self.next_btn.pack(side="right")

        row_tools = ctk.CTkFrame(self, fg_color="transparent")
        row_tools.pack(fill="x", padx=28, pady=(0, 12))
        self.row_column_menu = Theme.create_dropdown(row_tools, ["Sin columnas"], width=180)
        self.row_column_menu.pack(side="left", padx=4)
        self.row_condition_menu = Theme.create_dropdown(row_tools, ["==", "!=", ">", ">=", "<", "<=", "contains"], width=110)
        self.row_condition_menu.pack(side="left", padx=4)
        self.row_value_entry = Theme.create_input(row_tools, "Valor", width=140)
        self.row_value_entry.pack(side="left", padx=4)
        Theme.create_secondary_button(row_tools, "Preview eliminar", self._preview_delete_condition, width=150).pack(side="left", padx=4)
        Theme.create_danger_button(row_tools, "Eliminar por condicion", self._delete_condition, width=170).pack(side="left", padx=4)

        self.text_area = ctk.CTkTextbox(self, font=Theme.mono(12), height=430)
        self.text_area.pack(fill="both", expand=True, padx=28, pady=(0, 28))

    def _previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_preview()

    def _next_page(self):
        if self.dm.has_data():
            df = self._filtered_frame()
            max_page = max((len(df) - 1) // self.page_size, 0)
            if self.current_page < max_page:
                self.current_page += 1
                self._refresh_preview()

    def _filtered_frame(self):
        if not self.dm.has_data():
            return self.dm.df
        query = self.search_entry.get().strip().lower()
        if not query:
            return self.dm.df
        text_df = self.dm.df.astype(str).apply(lambda col: col.str.contains(query, case=False, na=False))
        return self.dm.df[text_df.any(axis=1)]

    def _refresh_preview(self):
        if not self.dm.has_data():
            self.text_area.configure(state="normal")
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", "Sin datos cargados.")
            self.text_area.configure(state="disabled")
            self.info_label.configure(text="Sin datos")
            return

        df = self._filtered_frame()
        total_pages = max((len(df) - 1) // self.page_size, 0) if len(df) else 0
        self.current_page = min(self.current_page, total_pages)
        start = self.current_page * self.page_size
        end = start + self.page_size
        page_df = df.iloc[start:end]

        self.info_label.configure(text=self.dm.get_shape_str())
        self.page_label.configure(text=f"Página {self.current_page + 1} / {total_pages + 1}")

        for key, label in self.stats_labels:
            if key == "rows":
                label.configure(text=f"{len(df):,}")
            elif key == "cols":
                label.configure(text=f"{len(df.columns)}")
            elif key == "nulls":
                label.configure(text=f"{int(df.isna().sum().sum()):,}")
            elif key == "duplicates":
                label.configure(text=f"{int(df.duplicated().sum()):,}")

        self.text_area.configure(state="normal")
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", page_df.to_string(index=False))
        self.text_area.configure(state="disabled")

        columns = [str(col) for col in self.dm.df.columns]
        self.row_column_menu.configure(values=columns)
        if self.row_column_menu.get() not in columns:
            self.row_column_menu.set(columns[0])

    def refresh(self):
        self._refresh_preview()

    def _condition_value(self):
        raw = self.row_value_entry.get()
        try:
            return float(raw)
        except ValueError:
            return raw

    def _preview_delete_condition(self):
        if not self.dm.has_data():
            return
        try:
            preview = self.engine.preview_drop_rows_by_condition(
                self.row_column_menu.get(),
                self.row_condition_menu.get(),
                self._condition_value(),
            )
            self.text_area.configure(state="normal")
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", f"Filas que se eliminarian: {len(preview):,}\n\n{preview.head(50).to_string(index=False)}")
            self.text_area.configure(state="disabled")
        except Exception as exc:
            messagebox.showerror("Eliminar filas", str(exc))

    def _delete_condition(self):
        if not self.dm.has_data():
            return
        try:
            preview = self.engine.preview_drop_rows_by_condition(
                self.row_column_menu.get(),
                self.row_condition_menu.get(),
                self._condition_value(),
            )
            if preview.empty:
                messagebox.showinfo("Eliminar filas", "La condicion no coincide con ninguna fila.")
                return
            if not messagebox.askyesno("Eliminar filas", f"Eliminar {len(preview):,} filas? Esta accion se puede deshacer."):
                return
            result = self.engine.drop_rows_by_condition(
                self.row_column_menu.get(),
                self.row_condition_menu.get(),
                self._condition_value(),
            )
            self.dm.apply_dataframe(result, "Eliminar filas por condicion")
            self.current_page = 0
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Eliminar filas", str(exc))
