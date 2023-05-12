from dataclasses import dataclass
from typing import List, Optional, Text

from .models import (
    Document,
    DocumentMetadataFilter,
    Query,
    QueryResult,
)


@dataclass
class UpsertCall:
    documents: List[Document]


@dataclass
class UpsertResponse:
    ids: List[Text]


@dataclass
class QueryCall:
    queries: List[Query]


@dataclass
class QueryResponse:
    results: List[QueryResult]


@dataclass
class DeleteCall:
    ids: Optional[List[Text]] = None
    filter: Optional[DocumentMetadataFilter] = None
    delete_all: Optional[bool] = False


@dataclass
class DeleteResponse:
    success: bool
