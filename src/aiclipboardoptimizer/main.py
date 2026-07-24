"""Main application entry point."""
import tkinter as tk
from tkinter import messagebox
import logging

from .config import AppConfig
from .gui import ClipboardOptimizerApp
from .utils.logging import configure_logging

logger = logging.getLogger(__name__)


def main() -> int:
    """Start the desktop application."""
    config = AppConfig.from_env()
    configure_logging(config.log_level)

    # Check for updates on startup
    try:
        from ..updater import check_and_update
        update_info = check_and_update()

        if update_info.get("available"):
            root = tk.Tk()
            root.withdraw()  # Hide window

            response = messagebox.askyesno(
                "Update Available",
                f"Version {update_info['version']} is available.\n\nUpdate now?"
            )

            if response:
                from ..updater import UpdateChecker
                tag = f"v{update_info['version']}"
                installer = UpdateChecker.download_installer(tag)
                if installer:
                    UpdateChecker.install_update(installer)
                    return 0  # Exit to let installer run

            root.destroy()
    except Exception as e:
        logger.error(f"Update check failed: {e}")
        # Continue app startup if update check fails

    root = tk.Tk()
    ClipboardOptimizerApp(root, config)
    root.mainloop()
    return 0
