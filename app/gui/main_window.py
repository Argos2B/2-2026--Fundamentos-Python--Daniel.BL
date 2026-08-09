"""Main application window container."""
import customtkinter as ctk
from app.core.data_manager import DataManager
from app.gui.sidebar import Sidebar
from app.gui.theme import Colors, Theme
from app.gui.import_view import ImportView
from app.gui.data_view import DataView
from app.gui.clean_view import CleanView
from app.gui.stats_view import StatsView
from app.gui.missing_view import MissingView
from app.gui.charts_view import ChartsView
from app.gui.export_view import ExportView

class MainWindow(ctk.CTk):
    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.dm = data_manager
        
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
            "import": ImportView(self.main_content, self.dm, on_imported=lambda: self._switch_view("data")),
            "data": DataView(self.main_content, self.dm),
            "clean": CleanView(self.main_content, self.dm),
            "stats": StatsView(self.main_content, self.dm),
            "missing": MissingView(self.main_content, self.dm),
            "charts": ChartsView(self.main_content, self.dm),
            "export": ExportView(self.main_content, self.dm)
        }
        
        self._current_view = None
        self._switch_view("import")
        
        # Register for updates
        self.dm.add_callback(self._on_data_change)
        
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
