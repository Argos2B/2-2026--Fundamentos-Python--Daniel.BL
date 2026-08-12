"""Import data workflow with detection, preview and dataset load."""
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog

from app.core.data_manager import DataManager
from app.core.import_manager import ImportManager
from app.gui.theme import Colors, Theme


class ImportView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager, on_imported=None):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.on_imported = on_imported
        self.import_manager = ImportManager()
        self.selected_paths: list[str] = []
        self.preview_dataframe = None
        self.preview_detection: dict = {}
        self.html_tables = []
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Importar datos", "📂").pack(anchor="w", padx=28, pady=(28, 18))

        upload_card = Theme.create_card(self)
        upload_card.pack(fill="x", padx=28, pady=(0, 14))
        upload_inner = ctk.CTkFrame(upload_card, fg_color="transparent")
        upload_inner.pack(fill="x", padx=24, pady=18)

        ctk.CTkLabel(
            upload_inner,
            text="Arrastra tus archivos aquí",
            font=Theme.heading(20),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            upload_inner,
            text="o",
            font=Theme.body(13),
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(8, 10))

        button_row = ctk.CTkFrame(upload_inner, fg_color="transparent")
        button_row.pack(anchor="w")
        Theme.create_primary_button(button_row, "+ Seleccionar archivos", command=self._browse_files, width=200, height=42).pack(side="left", padx=(0, 10))
        Theme.create_secondary_button(button_row, "Carpeta", command=self._browse_folder, width=160, height=42).pack(side="left", padx=(0, 10))
        Theme.create_secondary_button(button_row, "URL", command=self._import_from_url, width=120, height=42).pack(side="left", padx=(0, 10))
        Theme.create_secondary_button(button_row, "Pegar datos", command=self._paste_from_clipboard, width=140, height=42).pack(side="left")

        tags = ctk.CTkLabel(
            upload_inner,
            text="Soportado en esta instalacion: " + " · ".join(self.import_manager.supported_formats()).upper(),
            font=Theme.small(12),
            text_color=Colors.TEXT_MUTED,
            anchor="w",
        )
        tags.pack(anchor="w", pady=(18, 0))

        source_card = Theme.create_card(self)
        source_card.pack(fill="x", padx=28, pady=(0, 14))
        source_inner = ctk.CTkFrame(source_card, fg_color="transparent")
        source_inner.pack(fill="x", padx=18, pady=14)

        ctk.CTkLabel(source_inner, text="Métodos de importación", font=Theme.subheading(16), text_color=Colors.TEXT_PRIMARY).pack(anchor="w")
        connectors = ctk.CTkFrame(source_inner, fg_color="transparent")
        connectors.pack(fill="x", pady=(12, 0))

        for name, state in [
            ("Archivo", "Activo"),
            ("Carpeta", "Activo"),
            ("URL", "Activo"),
            ("Portapapeles", "Activo"),
        ]:
            chip = ctk.CTkFrame(connectors, fg_color=Colors.BG_INPUT, corner_radius=10)
            chip.pack(side="left", pady=4, padx=4)
            ctk.CTkLabel(chip, text=f"{name}  •  {state}", font=Theme.small(11), text_color=Colors.TEXT_SECONDARY, padx=10, pady=6).pack()

        preview_card = Theme.create_card(self)
        preview_card.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        preview_inner = ctk.CTkFrame(preview_card, fg_color="transparent")
        preview_inner.pack(fill="both", expand=True, padx=18, pady=16)

        self.selection_label = ctk.CTkLabel(preview_inner, text="Ningún archivo seleccionado", font=Theme.subheading(16), text_color=Colors.TEXT_PRIMARY, anchor="w")
        self.selection_label.pack(anchor="w")

        detection_frame = ctk.CTkFrame(preview_inner, fg_color="transparent")
        detection_frame.pack(fill="x", pady=(12, 10))

        self.format_label = ctk.CTkLabel(detection_frame, text="Formato detectado: —", font=Theme.body(13), text_color=Colors.TEXT_SECONDARY, anchor="w")
        self.format_label.grid(row=0, column=0, sticky="w", padx=(0, 20), pady=(0, 4))
        self.encoding_label = ctk.CTkLabel(detection_frame, text="Encoding: —", font=Theme.body(13), text_color=Colors.TEXT_SECONDARY, anchor="w")
        self.encoding_label.grid(row=0, column=1, sticky="w", padx=(0, 20), pady=(0, 4))
        self.delimiter_label = ctk.CTkLabel(detection_frame, text="Delimitador: —", font=Theme.body(13), text_color=Colors.TEXT_SECONDARY, anchor="w")
        self.delimiter_label.grid(row=0, column=2, sticky="w", pady=(0, 4))
        detection_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.search_entry = Theme.create_input(preview_inner, placeholder="Buscar en el preview", width=220)
        self.search_entry.pack(anchor="w", pady=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._apply_preview_filter)

        # Actions bar packed BEFORE the textbox with side='bottom' so it
        # stays visible even when the window shrinks.
        actions = ctk.CTkFrame(preview_inner, fg_color="transparent")
        actions.pack(side="bottom", fill="x", pady=(14, 4))
        Theme.create_primary_button(actions, "Importar dataset", command=self._confirm_import, width=180, height=42).pack(side="right")
        Theme.create_secondary_button(actions, "Cancelar", command=self._clear_preview, width=120, height=42).pack(side="right", padx=(0, 10))

        self.preview_text = ctk.CTkTextbox(preview_inner, height=150, font=Theme.mono(12), wrap="none")
        self.preview_text.pack(fill="both", expand=True)

    def _browse_files(self):
        paths = filedialog.askopenfilenames(title="Selecciona uno o varios archivos")
        if paths:
            self._process_paths(list(paths))

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Selecciona una carpeta para importar")
        if not folder:
            return
        files = []
        for root, _, names in os.walk(folder):
            for name in names:
                files.append(os.path.join(root, name))
        if files:
            self._process_paths(files)

    def _import_from_url(self):
        url = simpledialog.askstring("Importar desde URL", "Ingresa la URL del archivo:")
        if url:
            result = self.import_manager.import_url(url)
            if not result.get("success"):
                messagebox.showerror("URL", f"No se pudo importar desde URL:\n{result.get('error')}")
                return
            self.selected_paths = [url]
            self.preview_dataframe = result["dataframe"]
            self.preview_detection = result.get("metadata", {})
            self.html_tables = result.get("tables", [])
            self.selection_label.configure(text=url)
            self._update_detection_labels()
            self._apply_preview_filter()

    def _paste_from_clipboard(self):
        try:
            import tkinter as tk
            root = tk.Tk(); root.withdraw();
            data = root.clipboard_get(); root.destroy()
        except Exception:
            data = ""
        if not data:
            messagebox.showwarning("Portapapeles", "No hay datos válidos en el portapapeles.")
            return
        if data.strip().startswith("{") or data.strip().startswith("["):
            text_path = os.path.join(os.getcwd(), "clipboard_import.json")
            with open(text_path, "w", encoding="utf-8") as handle:
                handle.write(data)
            self._process_paths([text_path])
            return
        temp_path = os.path.join(os.getcwd(), "clipboard_import.csv")
        with open(temp_path, "w", encoding="utf-8") as handle:
            handle.write(data)
        self._process_paths([temp_path])

    def _process_paths(self, paths):
        self.selected_paths = [p for p in paths if os.path.exists(p)]
        if not self.selected_paths:
            messagebox.showerror("Error", "No se encontraron archivos válidos.")
            return

        try:
            if len(self.selected_paths) == 1:
                path = self.selected_paths[0]
                result = self.import_manager.import_file(path)
                if not result["success"]:
                    raise ValueError(result.get("error", "Formato no compatible."))
                self.preview_dataframe = result["dataframe"]
                self.preview_detection = result["metadata"]
                self.html_tables = result.get("tables", [])
                self.selection_label.configure(text=os.path.basename(path))
                self._update_detection_labels()
                self._apply_preview_filter()
                return

            results = self.import_manager.import_multiple(self.selected_paths)
            valid = [res for res in results if res.get("success")]
            if not valid:
                raise ValueError("No se pudo cargar ningún archivo válido.")
            dataframe = valid[0]["dataframe"]
            self.preview_dataframe = dataframe
            self.preview_detection = valid[0].get("metadata", {})
            self.selection_label.configure(text=f"{len(self.selected_paths)} archivos seleccionados")
            self._update_detection_labels()
            self._apply_preview_filter()
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo importar:\n{exc}")
            self.preview_dataframe = None
            self.preview_detection = {}
            self.selection_label.configure(text="Ningún archivo seleccionado")
            self._clear_text_preview()

    def _update_detection_labels(self):
        if self.preview_dataframe is None:
            self.format_label.configure(text="Formato detectado: —")
            self.encoding_label.configure(text="Encoding: —")
            self.delimiter_label.configure(text="Delimitador: —")
            return

        detection = self.preview_detection or {}
        format_name = str(detection.get("format", "desconocido")).upper()
        confidence = detection.get("confidence", 0.0)
        self.format_label.configure(text=f"Formato detectado: {format_name} ({confidence*100:.0f}%)")
        self.encoding_label.configure(text=f"Encoding: {detection.get('encoding', 'utf-8')}")
        self.delimiter_label.configure(text=f"Delimitador: {detection.get('delimiter', '—')}")

    def _apply_preview_filter(self, event=None):
        if self.preview_dataframe is None:
            self._clear_text_preview()
            return

        query = self.search_entry.get().strip().lower()
        df = self.preview_dataframe.copy()
        if query:
            text_df = df.astype(str).apply(lambda col: col.str.contains(query, case=False, na=False))
            df = df[text_df.any(axis=1)]

        preview = df.head(20)
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", preview.to_string(index=False))
        self.preview_text.configure(state="disabled")

    def _clear_text_preview(self):
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", "Selecciona un archivo para previsualizarlo.")
        self.preview_text.configure(state="disabled")

    def _clear_preview(self):
        self.selected_paths = []
        self.preview_dataframe = None
        self.preview_detection = {}
        self.search_entry.delete(0, "end")
        self.selection_label.configure(text="Ningún archivo seleccionado")
        self._update_detection_labels()
        self._clear_text_preview()

    def _confirm_import(self):
        if self.preview_dataframe is None:
            messagebox.showwarning("Sin datos", "Primero selecciona un archivo válido para importarlo.")
            return
        try:
            self.dm.load_dataframe(self.preview_dataframe, file_name=os.path.basename(self.selected_paths[0]) if self.selected_paths else "dataset")
            messagebox.showinfo("Importación completada", "Dataset cargado correctamente.")
            if self.on_imported:
                self.on_imported()
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo cargar el dataset:\n{exc}")
