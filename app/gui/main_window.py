"""Main application window container."""
import customtkinter as ctk

from app.core.data_manager import DataManager
from app.core.shortcuts_manager import ShortcutsManager
from app.gui.dashboard_view import DashboardView
from app.gui.sidebar import Sidebar
from app.gui.theme import Colors
from app.gui.import_view import ImportView
from app.gui.data_view import DataView
from app.gui.clean_view import CleanView
from app.gui.stats_view import StatsView
from app.gui.missing_view import MissingView
from app.gui.charts_view import ChartsView
from app.gui.export_view import ExportView
from app.gui.workflow_views import (
    CompareView,
    FilesView,
    HelpView,
    HistoryView,
    SettingsView,
    TrashView,
    ToolsView,
    TransformView,
)
from app.gui.project_view import ProjectView


class MainWindow(ctk.CTk):
    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.dm = data_manager
        self.shortcuts = ShortcutsManager()
        
        self.title("Data Analyzer Pro")
        self.geometry("1024x768")
        self.configure(fg_color=Colors.BG_PRIMARY)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Sidebar
        self.sidebar = Sidebar(self, on_navigate=self._switch_view)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Main content area
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew")
        
        # Views
        self.views = {
            "dashboard": DashboardView(self.main_content, self.dm, on_navigate=self._switch_view),
            "import": ImportView(self.main_content, self.dm, on_imported=lambda: self._switch_view("data")),
            "files": FilesView(self.main_content, self.dm, on_open=lambda: self._switch_view("data"), on_analyze=lambda: self._switch_view("stats")),
            "data": DataView(self.main_content, self.dm),
            "clean": CleanView(self.main_content, self.dm),
            "transform": TransformView(self.main_content, self.dm),
            "stats": StatsView(self.main_content, self.dm),
            "missing": MissingView(self.main_content, self.dm),
            "charts": ChartsView(self.main_content, self.dm),
            "compare": CompareView(self.main_content, self.dm),
            "tools": ToolsView(self.main_content, self.dm),
            "export": ExportView(self.main_content, self.dm),
            "history": HistoryView(self.main_content, self.dm),
            "settings": SettingsView(self.main_content, self.dm, on_theme_change=self._apply_theme),
            "projects": ProjectView(self.main_content, self.dm),
            "trash": TrashView(self.main_content, self.dm),
            "help": HelpView(self.main_content, self.dm),
        }

        self._current_view = None
        self._switch_view("dashboard")
        
        # Register for updates
        self.dm.add_callback(self._on_data_change)
        self._bind_shortcuts()
        
    def _switch_view(self, view_name: str):
        if self._current_view:
            self._current_view.pack_forget()
            
        self._current_view = self.views[view_name]
        self._current_view.pack(fill="both", expand=True)
        self.sidebar.set_active(view_name)
        
        # Trigger refresh on views that need it
        if hasattr(self._current_view, "refresh"):
            self._current_view.refresh()
            
    def _on_data_change(self):
        if hasattr(self._current_view, "refresh"):
            self._current_view.refresh()

    def _bind_shortcuts(self):
        mapping = {
            "open": lambda _event: self._switch_view("files"),
            "import": lambda _event: self._switch_view("import"),
            "export": lambda _event: self._switch_view("export"),
            "search": lambda _event: self._focus_search(),
            "undo": lambda _event: self.dm.undo(),
            "redo": lambda _event: self.dm.redo(),
            "save": lambda _event: self._switch_view("projects"),
            "new_analysis": lambda _event: self._switch_view("stats"),
            "open_project": lambda _event: self._switch_view("projects"),
        }
        for action, handler in mapping.items():
            self.bind(self.shortcuts.to_tk_sequence(self.shortcuts.get(action)), handler)

    def _focus_search(self):
        search = getattr(self._current_view, "search", None) or getattr(self._current_view, "search_entry", None)
        if search is not None:
            search.focus_set()

    def _apply_theme(self, value: str):
        import customtkinter as ctk

        ctk.set_appearance_mode(value)
        self.configure(fg_color=Colors.BG_PRIMARY)
        self.sidebar.configure(fg_color=Colors.BG_SIDEBAR)
