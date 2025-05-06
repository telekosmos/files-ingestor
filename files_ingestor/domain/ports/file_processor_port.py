from abc import ABC, abstractmethod
from collections.abc import Sequence

from llama_index.core.schema import BaseNode

from files_ingestor.application.commands import Command


class FileProcessorPort(ABC):
    @abstractmethod
    def process(self, command: Command) -> Sequence[BaseNode] | int:
        pass
