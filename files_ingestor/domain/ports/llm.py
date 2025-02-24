from abc import ABC, abstractmethod

from llama_index.core.llms.function_calling import FunctionCallingLLM


class FunctionCallingLLMPort(ABC):
    @abstractmethod
    def get_model(self) -> FunctionCallingLLM: ...
