from abc import ABC, abstractmethod
from typing import Any


class Command(ABC):
    @property
    @abstractmethod
    def name(self) -> Any: ...
