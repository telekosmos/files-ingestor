from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.llms.anthropic import Anthropic

import files_ingestor.domain.ports.config as ConfigPort
from files_ingestor.domain.ports.llm import FunctionCallingLLMPort
from files_ingestor.domain.ports.logger_port import LoggerPort


class AnthropicAdapter(FunctionCallingLLMPort):
    def __init__(self, config: ConfigPort, logger: LoggerPort):
        self.config = config
        self.logger = logger
        self.model_name = self.config.get("llm.anthropic.name")
        self.anthropic_model = Anthropic(
            model=self.model_name,
            api_key=self.config.get("llm.anthropic.api_key")
        )
        self.logger.info(f"Using Anthropic {self.model_name}")

    def get_model(self) -> FunctionCallingLLM:
        return self.anthropic_model
