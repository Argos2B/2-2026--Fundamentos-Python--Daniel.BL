"""Project management view with a unique layout."""
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox

from app.core.data_manager import DataManager
from app.core.project_manager import ProjectManager
from app.core.settings_manager import SettingsManager
from app.gui.theme import Colors, Theme


class ProjectView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.settings = SettingsManager()
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Gestor de Proyectos", "📂").pack(anchor="w", padx=28, pady=(28, 18))

        # Main layout: Left column for info, Right column for actions
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # Left Column: Project Info
        left_col = ctk.CTkFrame(content, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.info_card = Theme.create_card(left_col)
        self.info_card.pack(fill="both", expand=True)
        
        info_inner = ctk.CTkFrame(self.info_card, fg_color="transparent")
        info_inner.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(info_inner, text="Estado del Proyecto", font=Theme.subheading(18), text_color=Colors.TEXT_PRIMARY).pack(anchor="w", pady=(0, 20))
        
        self.status_frame = ctk.CTkFrame(info_inner, fg_color="transparent")
        self.status_frame.pack(fill="x")
        
        # We will populate status labels in refresh()
        self.lbl_name = self._create_info_row(self.status_frame, "Nombre:", "Sin proyecto")
        self.lbl_path = self._create_info_row(self.status_frame, "Ruta:", "---")
        self.lbl_dataset = self._create_info_row(self.status_frame, "Dataset activo:", "Ninguno")
        self.lbl_datasets_count = self._create_info_row(self.status_frame, "Datasets cargados:", "0")
        self.lbl_history = self._create_info_row(self.status_frame, "Historial:", "0 operaciones")

        # Right Column: Actions
        right_col = ctk.CTkFrame(content, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        actions_card = Theme.create_card(right_col)
        actions_card.pack(fill="both", expand=True)

        actions_inner = ctk.CTkFrame(actions_card, fg_color="transparent")
        actions_inner.pack(fill="both", expand=True, padx=20, pady=24)

        ctk.CTkLabel(actions_inner, text="Acciones", font=Theme.subheading(16), text_color=Colors.TEXT_PRIMARY).pack(anchor="w", pady=(0, 16))

        Theme.create_primary_button(actions_inner, "Nuevo proyecto", self._new_project, width=200).pack(pady=8)
        Theme.create_secondary_button(actions_inner, "Abrir proyecto", self._open_project, width=200).pack(pady=8)
        
        ctk.CTkFrame(actions_inner, fg_color=Colors.BORDER, height=1).pack(fill="x", pady=16)
        
        Theme.create_secondary_button(actions_inner, "Guardar", self._save_project, width=200).pack(pady=8)
        Theme.create_secondary_button(actions_inner, "Guardar como...", self._save_as, width=200).pack(pady=8)
        Theme.create_secondary_button(actions_inner, "Cerrar proyecto", self._close_project, width=200).pack(pady=8)

        self.refresh()

    def _create_info_row(self, parent, label_text, value_text):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=6)
        ctk.CTkLabel(row, text=label_text, font=Theme.body(14), text_color=Colors.TEXT_MUTED, width=150, anchor="w").pack(side="left")
        val_lbl = ctk.CTkLabel(row, text=value_text, font=Theme.body(14), text_color=Colors.TEXT_PRIMARY, anchor="w")
        val_lbl.pack(side="left", fill="x", expand=True)
        return val_lbl

    def _new_project(self):
        folder = filedialog.askdirectory(title="Selecciona la carpeta para el nuevo proyecto")
        if folder:
            try:
                self.dm.current_project = str(ProjectManager.create_project(folder))
                self.refresh()
                messagebox.showinfo("Proyecto", f"Proyecto creado en:\n{folder}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear el proyecto:\n{e}")

    def _open_project(self):
        folder = filedialog.askdirectory(title="Abrir proyecto")
        if folder:
            try:
                ProjectManager.load_project(folder, self.dm)
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el proyecto:\n{e}")

    def _save_project(self):
        if not self.dm.current_project:
            self._save_as()
            return
        try:
            ProjectManager.save_project(self.dm.current_project, self.dm, self.settings.all())
            self.refresh()
            messagebox.showinfo("Proyecto", "Proyecto guardado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el proyecto:\n{e}")

    def _save_as(self):
        folder = filedialog.askdirectory(title="Guardar proyecto como")
        if folder:
            try:
                self.dm.current_project = folder
                self._save_project()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el proyecto:\n{e}")
                
    def _close_project(self):
        if messagebox.askyesno("Cerrar proyecto", "¿Estás seguro de cerrar el proyecto actual? Asegúrate de haber guardado."):
            self.dm.current_project = None
            self.dm.df = None
            self.dm.original_df = None
            self.dm.file_name = None
            self.dm.file_path = None
            self.dm.datasets.clear()
            self.dm.history.clear()
            self.dm.notify()

    def refresh(self):
        if self.dm.current_project:
            name = os.path.basename(self.dm.current_project)
            path = self.dm.current_project
        else:
            name = "Sin proyecto"
            path = "---"
            
        dataset = self.dm.file_name or "Ninguno"
        datasets_count = str(len(self.dm.datasets))
        history_count = f"{len(self.dm.history.entries())} operaciones"
        
        self.lbl_name.configure(text=name)
        self.lbl_path.configure(text=path)
        self.lbl_dataset.configure(text=dataset)
        self.lbl_datasets_count.configure(text=datasets_count)
        self.lbl_history.configure(text=history_count)
