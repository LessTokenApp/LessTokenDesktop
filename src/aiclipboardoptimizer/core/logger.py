"""Centralized logging configuration."""
import logging
import sys
from pathlib import Path
from typing import Optional


class Logger:
    """Singleton logger factory with consistent formatting."""

    _loggers: dict[str, logging.Logger] = {}
    _config: Optional[dict] = None

    @classmethod
    def configure(cls, level: str = "INFO", log_dir: Optional[Path] = None) -> None:
        """Configure global logging settings.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR)
            log_dir: Optional directory for log files
        """
        cls._config = {"level": level, "log_dir": log_dir}
        # Clear existing loggers to reapply config
        for logger in cls._loggers.values():
            logger.handlers.clear()

    @classmethod
    def get(cls, name: str) -> logging.Logger:
        """Get or create logger with given name.

        Args:
            name: Logger name (typically __name__)

        Returns:
            Configured logger instance
        """
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)
        config = cls._config or {"level": "INFO", "log_dir": None}
        level = getattr(logging, config["level"].upper(), logging.INFO)
        logger.setLevel(level)

        # Console handler
        if not logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            # File handler if log_dir provided
            if config["log_dir"]:
                config["log_dir"].mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(
                    config["log_dir"] / f"{name.replace('.', '_')}.log"
                )
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

        cls._loggers[name] = logger
        return logger
