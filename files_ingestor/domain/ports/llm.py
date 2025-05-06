from abc import ABC, abstractmethod

from llama_index.core.llms.function_calling import FunctionCallingLLM


class FunctionCallingLLMPort(ABC):
    __SUPPORTED_LIBRARIES: list[str] = property(lambda self: ["llamaindex", "langchain"])

    @abstractmethod
    def get_model(self, library: str) -> FunctionCallingLLM: ...
