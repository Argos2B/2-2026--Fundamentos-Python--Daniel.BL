"""Charts view."""
import customtkinter as ctk
from app.core.data_manager import DataManager
from app.gui.theme import Theme
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class ChartsView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self._build_ui()

    def _build_ui(self):
        Theme.create_section_title(self, "Gráficos", "📉").pack(anchor="w", padx=30, pady=(30, 20))
        Theme.create_primary_button(self, "Generar Histograma (Primer Col Numérica)", command=self._plot).pack(pady=10)
        self.canvas_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.canvas_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
    def _plot(self):
        if not self.dm.has_data(): return
        
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
            
        num_cols = self.dm.df.select_dtypes(include='number').columns
        if len(num_cols) == 0: return
        
        Theme.apply_matplotlib_style()
        fig, ax = plt.subplots(figsize=(6, 4))
        self.dm.df[num_cols[0]].hist(ax=ax, bins=30, color="#6366F1")
        ax.set_title(f"Histograma de {num_cols[0]}")
        
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
