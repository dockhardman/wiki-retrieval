from dataclasses import dataclass
from typing import List, Optional, Text


@dataclass
class _WithScore:
    score: float


@dataclass
class _WithEmbedding:
    embedding: List[float]


@dataclass
class DocumentMetadata:
    name: Optional[Text] = None
    author: Optional[Text] = None
    created_at: Optional[Text] = None
    source: Optional[Text] = None
    source_id: Optional[Text] = None
    url: Optional[Text] = None

    def __post_init__(self):
        if self.author:
            self.author = self.author.strip()
        if self.created_at:
            self.created_at = self.created_at.strip()
        if self.source:
            self.source = self.source.strip()
        if self.source_id:
            self.source_id = self.source_id.strip()
        if self.url:
            self.url = self.url.strip()


@dataclass
class Document:
    text: Text
    id: Optional[Text] = None
    metadata: Optional[DocumentMetadata] = None


@dataclass
class DocumentWithEmbedding(Document, _WithEmbedding):
    pass


@dataclass
class DocumentWithScore(DocumentWithEmbedding, _WithScore):
    pass


@dataclass
class DocumentMetadataFilter:
    document_id: Optional[Text] = None
    source: Optional[Text] = None
    source_id: Optional[Text] = None
    author: Optional[Text] = None
    start_date: Optional[Text] = None
    end_date: Optional[Text] = None


@dataclass
class Query:
    query: Text
    filter: Optional[DocumentMetadataFilter] = None
    top_k: Optional[int] = 3


@dataclass
class QueryWithEmbedding(Query, _WithEmbedding):
    pass


@dataclass
class QueryResult:
    query: Text
    results: List[DocumentWithScore]
