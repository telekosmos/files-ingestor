from __future__ import annotations

from files_ingestor.application.commands.ingest_pdf import IngestPDFCmd
from files_ingestor.application.queries.question_query import QuestionQuery

# from files_ingestor.domain.services.question_service import QuestionService
from files_ingestor.domain.services.react_agent import ReactAgent


class QAHandler:
    """Handles the file-counting query."""

    def __init__(self, agent: ReactAgent):
        self.agent = agent

    def handle(self, query: 'QuestionQuery') -> str:  # noqa: UP037
        """Handles the query and invokes the domain service."""
        return self.agent.query(query.query)
