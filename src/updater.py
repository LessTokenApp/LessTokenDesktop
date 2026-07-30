"""Auto-update system for LessToken desktop app."""

import os
import json
import subprocess
import requests
from pathlib import Path
from packaging import version
import logging

logger = logging.getLogger(__name__)

GITHUB_REPO = "LessTokenApp/LessTokenDesktop"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
# Must match the git tag being released. If this lags behind, every user on
# the newest build is told to update to the version they are already running.
CURRENT_VERSION = "1.0.7"


class UpdateChecker:
    """Check and download updates from GitHub."""

    @staticmethod
    def get_latest_version() -> str | None:
        """Fetch latest version from GitHub."""
        try:
            response = requests.get(GITHUB_API, timeout=5)
            response.raise_for_status()
            data = response.json()

            if "tag_name" in data:
                return data["tag_name"].lstrip("v")
            return None
        except Exception as e:
            logger.error(f"Failed to check updates: {e}")
            return None

    @staticmethod
    def is_update_available() -> bool:
        """Check if new version is available."""
        latest = UpdateChecker.get_latest_version()
        if not latest:
            return False

        try:
            return version.parse(latest) > version.parse(CURRENT_VERSION)
        except Exception as e:
            logger.error(f"Version comparison failed: {e}")
            return False

    @staticmethod
    def download_installer(tag: str) -> Path | None:
        """Download installer from GitHub release."""
        try:
            download_url = (
                f"https://github.com/{GITHUB_REPO}/releases/download/{tag}/"
                "lesstoken-setup.exe"
            )

            installer_path = Path.home() / "Downloads" / "lesstoken-setup.exe"

            response = requests.get(download_url, timeout=30, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(installer_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Log progress
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            logger.info(f"Download progress: {percent:.1f}%")

            logger.info(f"Installer downloaded: {installer_path}")
            return installer_path

        except Exception as e:
            logger.error(f"Failed to download installer: {e}")
            return None

    @staticmethod
    def install_update(installer_path: Path) -> bool:
        """Run installer to update app."""
        try:
            # Run installer with administrative privileges
            subprocess.Popen(
                [str(installer_path)],
                shell=True
            )
            logger.info("Installer started")
            return True
        except Exception as e:
            logger.error(f"Failed to run installer: {e}")
            return False


class UpdateDialog:
    """UI for update notification (for PySide6 integration)."""

    def __init__(self, new_version: str, callback):
        self.new_version = new_version
        self.callback = callback

    def show_update_available(self):
        """Show update available dialog."""
        message = (
            f"A new version ({self.new_version}) is available!\n\n"
            "Would you like to update now?"
        )
        # This will be integrated with PySide6 MessageBox
        return message


def check_and_update():
    """Main update check function - call on app startup."""
    logger.info(f"Current version: {CURRENT_VERSION}")

    if UpdateChecker.is_update_available():
        latest = UpdateChecker.get_latest_version()
        logger.info(f"Update available: {latest}")

        # In full implementation, show dialog and get user confirmation
        # For now, log it
        return {
            "available": True,
            "version": latest,
            "current": CURRENT_VERSION
        }

    logger.info("No updates available")
    return {"available": False, "version": CURRENT_VERSION}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = check_and_update()
    print(json.dumps(result, indent=2))
