import logging

from files_ingestor.domain.ports.logger_port import LoggerPort


class NullLoggerAdapter(LoggerPort):
    def __init__(self, logger_name: str = "files_ingestor", log_level: int = logging.INFO) -> None:
        """
        Initialize the logger with a specific name and log level.

        :param logger_name: Name of the logger (default: 'files_ingestor.')
        :param log_level: Logging level (default: logging.INFO)
        """
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(log_level)

    def debug(self, message: str) -> None:
        """
        Log a debug message.

        :param message: Debug message to log
        """
        pass

    def info(self, message: str) -> None:
        """
        Log an info message.

        :param message: Info message to log
        """
        pass

    def warn(self, message: str) -> None:
        """
        Log a warning message.

        :param message: Warning message to log
        """
        pass

    def error(self, message: str, error: Exception) -> None:
        """
        Log an error message with an exception.

        :param message: Error message to log
        :param error: Exception associated with the error
        """
        pass
