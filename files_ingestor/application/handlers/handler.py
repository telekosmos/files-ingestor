from abc import ABC, abstractmethod
from typing import Any, Optional

from files_ingestor.application.commands import Command


class Handler(ABC):
    @abstractmethod
    def handle(self, cmd: Command) -> Any: ...
