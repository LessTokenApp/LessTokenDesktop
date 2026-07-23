"""Desktop application entry point."""
import sys
import os

from PySide6.QtWidgets import QApplication

from .application import Application
from .config import AppConfig
from .ui.main_window import MainWindow
from .core.logger import Logger

logger = Logger.get(__name__)


def run_desktop_app() -> int:
    """Run desktop application.

    Returns:
        Exit code
    """
    try:
        # Load configuration
        config = AppConfig.from_env()
        logger.info(f"Starting {config.app_name}")

        # Create application instance
        app = Application(config)
        app.startup()

        # Create Qt application
        qt_app = QApplication(sys.argv)

        # Create main window
        window = MainWindow(app)
        window.show()

        logger.info("Desktop app started successfully")

        # Run event loop
        exit_code = qt_app.exec()

        # Shutdown
        app.shutdown()

        return exit_code

    except Exception as e:
        logger.error(f"Failed to start desktop app: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(run_desktop_app())
