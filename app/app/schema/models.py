from dataclasses import dataclass
from typing import List, Optional, Text


@dataclass
class _WithScore:
    score: float


@dataclass
class _WithChunks:
    chunks: List["DocumentChunk"]


@dataclass
class _WithEmbedding:
    embedding: List[float]


@dataclass
class DocumentMetadata:
    author: Optional[Text] = None
    created_at: Optional[Text] = None
    source: Optional[Text] = None
    source_id: Optional[Text] = None
    url: Optional[Text] = None


@dataclass
class DocumentChunkMetadata(DocumentMetadata):
    document_id: Optional[Text] = None


@dataclass
class DocumentChunk:
    metadata: DocumentChunkMetadata
    text: str
    embedding: Optional[List[float]] = None
    id: Optional[Text] = None


@dataclass
class DocumentChunkWithScore(DocumentChunk, _WithScore):
    pass


@dataclass
class Document:
    text: str
    id: Optional[Text] = None
    metadata: Optional[DocumentMetadata] = None


@dataclass
class DocumentWithChunks(Document, _WithChunks):
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
    query: str
    filter: Optional[DocumentMetadataFilter] = None
    top_k: Optional[int] = 3


@dataclass
class QueryWithEmbedding(Query, _WithEmbedding):
    pass


@dataclass
class QueryResult:
    query: str
    results: List[DocumentChunkWithScore]
