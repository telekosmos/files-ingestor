from abc import ABC, abstractmethod

from files_ingestor.application.commands import Command


class FileProcessorPort(ABC):
    @abstractmethod
    def process(self, command: Command, operations: list[str]) -> dict:
        pass
