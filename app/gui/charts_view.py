"""Minimal dark candlestick view for Visualizaciones."""

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from app.core.data_manager import DataManager
from app.core.ohlc_detector import detect_ohlc
from app.gui.chart_renderer import render_candlestick_chart
from app.gui.theme import Colors, Theme


class ChartsView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.canvas = None
        self.fig = None
        self.current_df = None
        self.current_metadata = {}
        self.story_texts = ["Just", "a", "bad", "day,", "is", "not", "a", "bad", "life"]
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        Theme.create_section_title(self, "Visualizaciones", "📈").pack(anchor="w", padx=28, pady=(28, 12))

        self.chart_card = Theme.create_card(self)
        self.chart_card.pack(fill="both", expand=True, padx=28, pady=(0, 28))
        self.chart_card.grid_rowconfigure(0, weight=1)
        self.chart_card.grid_columnconfigure(0, weight=1)

        self.canvas_frame = ctk.CTkFrame(self.chart_card, fg_color="transparent")
        self.canvas_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        self._show_placeholder(
            "Importa un dataset OHLC válido para ver la gráfica de velas.\n\n"
            "La sección Visualizaciones ahora es una única vista minimalista.",
        )

    def refresh(self):
        self.current_df = self.dm.df if self.dm.has_data() else None
        self.current_metadata = detect_ohlc(self.current_df) if self.current_df is not None else {}
        self._render_candlestick_view()

    def _render_candlestick_view(self):
        self._clear_canvas_area()

        if self.current_df is None or self.current_df.empty:
            self._show_placeholder("No hay datos disponibles para mostrar la gráfica.", error=True)
            return

        if not self.current_metadata.get("is_ohlc"):
            self._show_placeholder(
                "El dataset actual no contiene columnas OHLC válidas.\n\n"
                "Busca columnas de Fecha, Open, High, Low y Close."
            )
            return

        metadata = {
            "timestamp_column": self.current_metadata["timestamp_column"],
            "open_column": self.current_metadata["open_column"],
            "high_column": self.current_metadata["high_column"],
            "low_column": self.current_metadata["low_column"],
            "close_column": self.current_metadata["close_column"],
            "volume_column": self.current_metadata.get("volume_column"),
        }

        try:
            self.fig = render_candlestick_chart(
                self.current_df,
                metadata,
                style="Neon Candlestick",
                options={"grid": False, "legend": False, "tooltip": False, "labels": False, "sma": False},
                story_texts=self.story_texts,
            )
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill="both", expand=True)
            self.canvas.get_tk_widget().pack_propagate(False)
        except Exception as exc:
            self._show_placeholder(f"No se pudo generar la gráfica.\nDetalles: {exc}", error=True)

    def _show_placeholder(self, message: str, error: bool = False):
        self._clear_canvas_area()
        lbl = Theme.create_label(self.canvas_frame, message, style="body", anchor="center")
        if error:
            lbl.configure(text_color=Colors.ERROR)
        lbl.pack(expand=True)

    def _clear_canvas_area(self):
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.fig:
            plt.close(self.fig)
            self.fig = None
