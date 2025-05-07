from files_ingestor.domain.ports.file_reader_port import FileReaderPort


class FileReaderAdapter(FileReaderPort):
    """Implementation of the file reader port."""

    def read(self, file_name: str) -> str:
        """Reads the content of a file and returns it."""
        try:
            with open(file_name) as file:
                return file.read()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File '{file_name}' not found.") from e  # noqa: TRY003
