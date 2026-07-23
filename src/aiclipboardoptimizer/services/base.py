"""Base service class for all application services."""
from abc import ABC, abstractmethod
from ..core.logger import Logger

logger = Logger.get(__name__)


class BaseService(ABC):
    """Abstract base class for all application services.

    Services contain business logic and coordinate with repositories/providers.
    They should be stateless and testable.
    """

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Unique service name."""
        pass

    def on_startup(self) -> None:
        """Called when service starts. Override in subclasses."""
        logger.info(f"Service started: {self.service_name}")

    def on_shutdown(self) -> None:
        """Called when service shuts down. Override in subclasses."""
        logger.info(f"Service stopped: {self.service_name}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.service_name})"
