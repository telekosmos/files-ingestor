from typing import Any, Optional

import config

from files_ingestor.domain.ports.config import ConfigPort


class ConfigConfig(ConfigPort):
    def __init__(self, file_path: str | None = "config.json") -> None:
        self.file_path = file_path
        self.cfg = config.Config(file_path)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        try:    
            return self.cfg[key]
        except config.ConfigError as ce:
            if default is not None:
                return default
            else:
                raise ce




