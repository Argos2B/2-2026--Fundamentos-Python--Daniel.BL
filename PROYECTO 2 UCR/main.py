"""Entry point for the UCR project."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def main() -> None:
    import customtkinter as ctk

    from app.core.data_manager import DataManager
    from app.gui.main_window import MainWindow

    ctk.set_appearance_mode("dark")
    dm = DataManager.get_instance()
    app = MainWindow(dm)
    app.mainloop()


if __name__ == "__main__":
    main()
