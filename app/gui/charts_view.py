"""Charts view with full configuration panel and dynamic rendering."""
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

from app.core.data_manager import DataManager
from app.core.ohlc_detector import detect_ohlc, resample_ohlc, validate_ohlc
from app.gui.chart_renderer import render_candlestick_chart, render_standard_chart
from app.gui.theme import Colors, Theme
from app.core.settings_manager import SettingsManager

class ChartsView(ctk.CTkFrame):
    def __init__(self, parent, data_manager: DataManager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.settings = SettingsManager()
        self.canvas = None
        self.toolbar = None
        self.fig = None
        
        # UI variables
        self.var_dataset = ctk.StringVar()
        self.var_chart_type = ctk.StringVar(value="Line")
        self.var_style = ctk.StringVar(value="Profesional")
        
        # Column variables
        self.var_col_x = ctk.StringVar()
        self.var_col_y = ctk.StringVar()
        self.var_col_date = ctk.StringVar()
        self.var_col_open = ctk.StringVar()
        self.var_col_high = ctk.StringVar()
        self.var_col_low = ctk.StringVar()
        self.var_col_close = ctk.StringVar()
        self.var_col_vol = ctk.StringVar()
        
        # Options variables
        self.var_opt_grid = ctk.BooleanVar(value=True)
        self.var_opt_legend = ctk.BooleanVar(value=True)
        self.var_opt_tooltip = ctk.BooleanVar(value=True)
        self.var_opt_labels = ctk.BooleanVar(value=False)
        self.var_opt_zoom = ctk.BooleanVar(value=True)
        self.var_opt_nav = ctk.BooleanVar(value=True)
        self.var_opt_sma = ctk.BooleanVar(value=False)
        
        self.current_df = None
        self.current_metadata = {}
        
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        Theme.create_section_title(self, "Gráficas", "📉").pack(anchor="w", padx=28, pady=(28, 12))

        # Main layout: Left (Config) / Right (Canvas)
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        content.grid_columnconfigure(0, weight=1, minsize=300)
        content.grid_columnconfigure(1, weight=4)
        content.grid_rowconfigure(0, weight=1)

        # Left Column: Configuration
        self._build_config_panel(content)
        
        # Right Column: Chart Area
        self._build_chart_area(content)

    def _build_config_panel(self, parent):
        config_card = Theme.create_card(parent)
        config_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        scroll = ctk.CTkScrollableFrame(config_card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Dataset
        Theme.create_label(scroll, "Dataset:", style="secondary").pack(anchor="w", pady=(0, 4))
        self.cb_dataset = Theme.create_dropdown(scroll, [], command=self._on_dataset_changed)
        self.cb_dataset.pack(fill="x", pady=(0, 16))
        
        # Chart Type
        Theme.create_label(scroll, "Tipo de gráfico:", style="secondary").pack(anchor="w", pady=(0, 4))
        chart_types = ["Line", "Bar", "Area", "Scatter", "Histogram", "Pie", "Donut", "Boxplot", "Heatmap", "Candlestick", "OHLC"]
        self.cb_chart_type = Theme.create_dropdown(scroll, chart_types, variable=self.var_chart_type, command=self._on_chart_type_changed)
        self.cb_chart_type.pack(fill="x", pady=(0, 16))
        
        # Style (only for candlestick)
        self.style_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        Theme.create_label(self.style_frame, "Estilo:", style="secondary").pack(anchor="w", pady=(0, 4))
        self.cb_style = Theme.create_dropdown(self.style_frame, ["Profesional", "Neon Candlestick"], variable=self.var_style)
        self.cb_style.pack(fill="x", pady=(0, 16))
        # Initial pack handled in _update_config_fields
        
        # Columns Section
        Theme.create_label(scroll, "Columnas:", style="subheading").pack(anchor="w", pady=(10, 8))
        self.cols_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.cols_frame.pack(fill="x")
        
        # We will dynamically populate cols_frame in _update_config_fields
        
        # Generate Button
        Theme.create_primary_button(scroll, "GENERAR GRÁFICA", command=self._generate_chart).pack(fill="x", pady=(24, 10))
        
        # Help text
        self.lbl_help = Theme.create_label(scroll, "", style="small")
        self.lbl_help.pack(fill="x", pady=(10, 0))

    def _build_chart_area(self, parent):
        right_col = ctk.CTkFrame(parent, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew")
        
        self.chart_card = Theme.create_card(right_col)
        self.chart_card.pack(fill="both", expand=True)
        
        self.canvas_frame = ctk.CTkFrame(self.chart_card, fg_color="transparent")
        self.canvas_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Options below chart
        opts_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        opts_frame.pack(fill="x", pady=(10, 0))
        
        # Checkboxes
        checks_frame = ctk.CTkFrame(opts_frame, fg_color="transparent")
        checks_frame.pack(side="left", fill="x", expand=True)
        
        def create_check(parent, text, var):
            cb = ctk.CTkCheckBox(parent, text=text, variable=var, text_color=Colors.TEXT_PRIMARY, fg_color=Colors.ACCENT)
            cb.pack(side="left", padx=8)
            return cb
            
        create_check(checks_frame, "Cuadrícula", self.var_opt_grid)
        create_check(checks_frame, "Leyenda", self.var_opt_legend)
        create_check(checks_frame, "Tooltips", self.var_opt_tooltip)
        create_check(checks_frame, "Etiquetas", self.var_opt_labels)
        create_check(checks_frame, "SMA 20", self.var_opt_sma)
        
        # Buttons
        btns_frame = ctk.CTkFrame(opts_frame, fg_color="transparent")
        btns_frame.pack(side="right")
        
        Theme.create_secondary_button(btns_frame, "Guardar gráfico", command=self._save_chart).pack(side="left", padx=4)
        Theme.create_secondary_button(btns_frame, "Exportar", command=self._export_chart).pack(side="left", padx=4)
        Theme.create_secondary_button(btns_frame, "Restablecer", command=self._reset_view).pack(side="left", padx=4)

    def refresh(self):
        datasets = list(self.dm.datasets.keys())
        if self.dm.file_name and self.dm.file_name not in datasets:
            datasets.insert(0, self.dm.file_name)
            
        if not datasets:
            self.cb_dataset.configure(values=["Sin datos"])
            self.var_dataset.set("Sin datos")
            self._show_placeholder("No hay datasets cargados.\nVe a la pestaña Importar para cargar datos.")
            self.current_df = None
            self._update_config_fields()
            return
            
        self.cb_dataset.configure(values=datasets)
        if not self.var_dataset.get() or self.var_dataset.get() not in datasets:
            self.var_dataset.set(self.dm.file_name if self.dm.file_name else datasets[0])
            
        self._on_dataset_changed(self.var_dataset.get())

    def _get_real_column_choices(self):
        if self.current_df is None:
            return [""]

        columns = []
        for column in self.current_df.columns:
            value = str(column).strip()
            if value:
                columns.append(value)

        return [""] + columns

    def _on_dataset_changed(self, value):
        self.var_dataset.set(value)
        if value == self.dm.file_name:
            self.current_df = self.dm.df
        else:
            self.current_df = self.dm.datasets.get(value)
            
        if self.current_df is not None:
            self.current_metadata = detect_ohlc(self.current_df)
            # Auto-switch to Candlestick if OHLC detected and currently not selected
            if self.current_metadata.get("is_ohlc"):
                self.var_chart_type.set("Candlestick")
                self.cb_chart_type.set("Candlestick")
            
        self._update_config_fields()

    def _on_chart_type_changed(self, value):
        self.var_chart_type.set(value)
        self._update_config_fields()

    def _update_config_fields(self):
        for widget in self.cols_frame.winfo_children():
            widget.destroy()
            
        chart_type = self.var_chart_type.get()
        cols = []
        if self.current_df is not None:
            cols = [""] + list(self.current_df.columns)
            
        if chart_type in ["Candlestick", "OHLC"]:
            self.style_frame.pack(fill="x", pady=(0, 16))
            self.lbl_help.configure(text=(
                "Carga tu CSV con columnas OHLC para ver velas verdes/rojas.\n"
                "Open = apertura\n"
                "High = máximo\n"
                "Low = mínimo\n"
                "Close = cierre\n\n"
                "Este gráfico está pensado como una vista de trading profesional basada en datos de precios."
            ))
            
            # Helper to create column selector
            def create_col_selector(label, var, default_val=None):
                Theme.create_label(self.cols_frame, label, style="small").pack(anchor="w", pady=(6, 2))
                cb = Theme.create_dropdown(self.cols_frame, cols, variable=var)
                cb.pack(fill="x")
                if default_val and default_val in cols:
                    var.set(default_val)
                    cb.set(default_val)
                elif not var.get() or var.get() not in cols:
                    var.set("")
                    cb.set("")
                    
            create_col_selector("Fecha:", self.var_col_date, self.current_metadata.get("timestamp_column"))
            create_col_selector("Open:", self.var_col_open, self.current_metadata.get("open_column"))
            create_col_selector("High:", self.var_col_high, self.current_metadata.get("high_column"))
            create_col_selector("Low:", self.var_col_low, self.current_metadata.get("low_column"))
            create_col_selector("Close:", self.var_col_close, self.current_metadata.get("close_column"))
            create_col_selector("Volume (Opcional):", self.var_col_vol, self.current_metadata.get("volume_column"))
            
        else:
            self.style_frame.pack_forget()
            self.lbl_help.configure(text="")

            # Build clean column list from the currently loaded dataset
            real_columns = []
            if self.current_df is not None:
                real_columns = [str(col).strip() for col in self.current_df.columns if str(col).strip()]

            # Columna horizontal (X) — "Esperando datos..." when no data
            Theme.create_label(self.cols_frame, "Columna horizontal (Opcional):", style="small").pack(anchor="w", pady=(6, 2))
            if real_columns:
                x_values = [""] + real_columns
                cb_x = Theme.create_dropdown(self.cols_frame, x_values, variable=self.var_col_x)
                cb_x.pack(fill="x")
                if not self.var_col_x.get() or self.var_col_x.get() not in x_values:
                    self.var_col_x.set("")
                    cb_x.set("")
            else:
                cb_x = Theme.create_dropdown(self.cols_frame, ["Esperando datos..."], variable=self.var_col_x)
                cb_x.pack(fill="x")
                self.var_col_x.set("Esperando datos...")
                cb_x.set("Esperando datos...")

            # Columna vertical (Y) — "Esperando datos..." when no data
            Theme.create_label(self.cols_frame, "Columna vertical:", style="small").pack(anchor="w", pady=(6, 2))
            if real_columns:
                cb_y = Theme.create_dropdown(self.cols_frame, real_columns, variable=self.var_col_y)
                cb_y.pack(fill="x")
                if not self.var_col_y.get() or self.var_col_y.get() not in real_columns or self.var_col_y.get() == "Esperando datos...":
                    self.var_col_y.set(real_columns[0])
                    cb_y.set(real_columns[0])
            else:
                cb_y = Theme.create_dropdown(self.cols_frame, ["Esperando datos..."], variable=self.var_col_y)
                cb_y.pack(fill="x")
                self.var_col_y.set("Esperando datos...")
                cb_y.set("Esperando datos...")

    def _show_placeholder(self, message: str, error=False):
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
        if self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None
        if self.fig:
            plt.close(self.fig)
            self.fig = None

    def _generate_chart(self):
        if self.current_df is None or self.current_df.empty:
            self._show_placeholder("No hay datos disponibles.", error=True)
            return
            
        chart_type = self.var_chart_type.get()
        
        # Fetch options
        options = {
            "grid": self.var_opt_grid.get(),
            "legend": self.var_opt_legend.get(),
            "tooltip": self.var_opt_tooltip.get(),
            "labels": self.var_opt_labels.get(),
            "sma": self.var_opt_sma.get(),
        }
        
        self._clear_canvas_area()
        
        try:
            if chart_type in ["Candlestick", "OHLC"]:
                req_cols = {
                    "Fecha": self.var_col_date.get(),
                    "Open": self.var_col_open.get(),
                    "High": self.var_col_high.get(),
                    "Low": self.var_col_low.get(),
                    "Close": self.var_col_close.get(),
                }
                
                missing = [k for k, v in req_cols.items() if not v]
                if missing:
                    self._show_placeholder(f"No se puede crear la gráfica {chart_type}.\nFaltan las columnas:\n{', '.join(missing)}", error=True)
                    return
                    
                meta = {
                    "is_ohlc": True,
                    "timestamp_column": req_cols["Fecha"],
                    "open_column": req_cols["Open"],
                    "high_column": req_cols["High"],
                    "low_column": req_cols["Low"],
                    "close_column": req_cols["Close"],
                    "volume_column": self.var_col_vol.get() if self.var_col_vol.get() else None,
                }
                
                val = validate_ohlc(self.current_df, meta)
                if not val["valid"]:
                    self._show_placeholder("Datos inválidos:\n" + "\n".join(val["errors"]), error=True)
                    return
                    
                # Create Candlestick
                self.fig = render_candlestick_chart(
                    self.current_df, 
                    meta, 
                    style=self.var_style.get(),
                    options=options
                )
                
            else:
                col_y = self.var_col_y.get()
                col_x = self.var_col_x.get() if self.var_col_x.get() else None
                
                if not col_y:
                    self._show_placeholder("Debes seleccionar una columna vertical válida.", error=True)
                    return
                    
                self.fig = render_standard_chart(
                    self.current_df,
                    chart_type,
                    col_x,
                    col_y,
                    options=options
                )
                
            # Render to Tkinter
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill="both", expand=True)
            self.canvas.get_tk_widget().pack_propagate(False)
            
            if self.var_opt_nav.get():
                self.toolbar = NavigationToolbar2Tk(self.canvas, self.canvas_frame)
                self.toolbar.update()
                self.toolbar.pack(side="top", fill="x")
                # Hide default Tkinter navigation if you want a cleaner look, but we keep it for Pan/Zoom as requested
            
        except Exception as e:
            self._show_placeholder(f"No se pudo generar la gráfica.\nDetalles: {e}", error=True)

    def _save_chart(self):
        if not self.dm.has_data() or self.fig is None:
            messagebox.showwarning("Guardar gráfico", "No hay gráfica para guardar.")
            return
            
        title = simpledialog.askstring("Guardar gráfico", "Título de la gráfica:", initialvalue=f"{self.var_chart_type.get()} - {self.var_dataset.get()}")
        if not title:
            return
            
        chart_data = {
            "title": title,
            "type": self.var_chart_type.get(),
            "dataset": self.var_dataset.get(),
            "style": self.var_style.get(),
            "options": {
                "grid": self.var_opt_grid.get(),
                "legend": self.var_opt_legend.get(),
                "tooltip": self.var_opt_tooltip.get(),
                "labels": self.var_opt_labels.get(),
            },
            "columns": {
                "date": self.var_col_date.get(),
                "open": self.var_col_open.get(),
                "high": self.var_col_high.get(),
                "low": self.var_col_low.get(),
                "close": self.var_col_close.get(),
                "volume": self.var_col_vol.get(),
                "x": self.var_col_x.get(),
                "y": self.var_col_y.get()
            }
        }
        
        try:
            saved = self.dm.save_chart(chart_data)
            messagebox.showinfo("Guardar", f"Gráfico '{title}' guardado correctamente en el proyecto.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")
        
    def _export_chart(self):
        if self.fig is None:
            messagebox.showwarning("Exportar", "No hay gráfica para exportar.")
            return
            
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("SVG", "*.svg"), ("PDF", "*.pdf")],
        )
        if not path:
            return
            
        try:
            facecolor = self.fig.get_facecolor()
            self.fig.savefig(path, bbox_inches="tight", facecolor=facecolor, edgecolor='none')
            messagebox.showinfo("Exportar", f"Gráfica exportada exitosamente a:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar la gráfica:\n{e}")

    def _reset_view(self):
        if self.toolbar:
            self.toolbar.home()
        elif self.canvas:
            self.canvas.draw()
