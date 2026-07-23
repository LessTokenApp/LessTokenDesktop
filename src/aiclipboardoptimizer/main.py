"""Main application entry point."""
import tkinter as tk

from .config import AppConfig
from .gui import ClipboardOptimizerApp
from .utils.logging import configure_logging


def main() -> int:
    """Start the desktop application."""
    config = AppConfig.from_env()
    configure_logging(config.log_level)

    root = tk.Tk()
    ClipboardOptimizerApp(root, config)
    root.mainloop()
    return 0
