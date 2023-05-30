import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Text

from app.config import settings


@dataclass
class _WithScore:
    score: float


@dataclass
class _WithEmbedding:
    embedding: List[float]


@dataclass
class Document:
    text: Text
    id: Optional[Text] = None
    metadata: Optional[Dict[Text, Any]] = None

    def __post_init__(self):
        if self.id:
            self.id = self.id.strip()
        else:
            self.id = str(uuid.uuid4())
        if self.text:
            self.text = self.text.strip()
        self.metadata = self.metadata or {}

    def with_embedding(self, embedding: List[float]) -> "DocumentWithEmbedding":
        return DocumentWithEmbedding(
            id=self.id,
            text=self.text,
            metadata=self.metadata,
            embedding=embedding,
        )


@dataclass
class DocumentWithEmbedding(Document, _WithEmbedding):
    pass


@dataclass
class DocumentWithScore(DocumentWithEmbedding, _WithScore):
    pass


@dataclass
class Query:
    query: Text
    filter: Optional[Dict[Text, Any]] = None
    top_k: Optional[int] = 5

    def __post_init__(self):
        self.query = self.query.strip()
        self.filter = self.filter or {}
        self.top_k = min(self.top_k, settings.max_top_k)

    def with_embedding(self, embedding: List[float]) -> "QueryWithEmbedding":
        return QueryWithEmbedding(
            query=self.query,
            filter=self.filter,
            top_k=self.top_k,
            embedding=embedding,
        )


@dataclass
class QueryWithEmbedding(Query, _WithEmbedding):
    pass


@dataclass
class QueryResult:
    query: Text
    results: List[DocumentWithScore]
