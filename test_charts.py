import os
import pandas as pd
import customtkinter as ctk

from app.core.data_manager import DataManager
from app.gui.charts_view import ChartsView

def test_charts():
    # 1. Create realistic dataset
    data = {
        "Fecha": pd.date_range(start="2024-01-01", periods=10, freq="D"),
        "Open": [100, 102, 101, 105, 104, 108, 107, 110, 109, 112],
        "High": [103, 104, 106, 106, 109, 109, 112, 111, 115, 114],
        "Low": [99, 100, 99, 103, 102, 105, 106, 108, 108, 110],
        "Close": [102, 101, 105, 104, 108, 107, 110, 109, 112, 113],
        "Volume": [1000, 1200, 900, 1500, 1100, 1300, 1400, 1600, 1200, 1800]
    }
    df = pd.DataFrame(data)
    
    # 2. Setup DataManager
    dm = DataManager()
    dm.df = df
    dm.file_name = "test_stock_data.csv"
    dm.datasets["test_stock_data.csv"] = df
    
    # 3. Create GUI (headless-ish)
    app = ctk.CTk()
    app.geometry("1000x800")
    
    # 4. Instantiate ChartsView
    view = ChartsView(app, dm)
    view.pack(fill="both", expand=True)
    
    print("Columns detected:")
    print("Date:", view.var_col_date.get())
    print("Open:", view.var_col_open.get())
    print("High:", view.var_col_high.get())
    print("Low:", view.var_col_low.get())
    print("Close:", view.var_col_close.get())
    print("Volume:", view.var_col_vol.get())
    
    # 5. Generate Professional Candlestick
    view.var_style.set("Profesional")
    view._generate_chart()
    
    if view.fig:
        view.fig.savefig("test_candlestick_pro.png")
        print("Generated test_candlestick_pro.png")
    else:
        print("Failed to generate Pro chart")
        
    # 6. Generate Neon Candlestick
    view.var_style.set("Neon Candlestick")
    view._generate_chart()
    
    if view.fig:
        facecolor = view.fig.get_facecolor()
        view.fig.savefig("test_candlestick_neon.png", facecolor=facecolor, edgecolor='none')
        print("Generated test_candlestick_neon.png")
    else:
        print("Failed to generate Neon chart")
        
    # 7. Generate standard chart
    view.var_chart_type.set("Line")
    view._on_chart_type_changed("Line")
    view.var_col_x.set("Fecha")
    view.var_col_y.set("Close")
    view._generate_chart()
    
    if view.fig:
        view.fig.savefig("test_line.png")
        print("Generated test_line.png")
    else:
        print("Failed to generate Line chart")
        
    # app.mainloop() # don't block
    
if __name__ == "__main__":
    test_charts()
