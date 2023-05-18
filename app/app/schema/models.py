import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Text


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

    def to_document_with_embedding(
        self, embedding: List[float]
    ) -> "DocumentWithEmbedding":
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
    top_k: Optional[int] = 3


@dataclass
class QueryWithEmbedding(Query, _WithEmbedding):
    pass


@dataclass
class QueryResult:
    query: Text
    results: List[DocumentWithScore]
