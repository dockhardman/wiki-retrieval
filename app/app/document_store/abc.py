from abc import ABC, abstractmethod
from typing import List, Optional, Text

from app.schema.models import (
    Document,
    DocumentMetadataFilter,
    Query,
    QueryResult,
)


class DocumentStore(ABC):
    @property
    def host(self) -> str:
        raise NotImplementedError

    @property
    def port(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def touch(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def upsert(
        self, documents: List[Document], chunk_token_size: Optional[int] = None
    ) -> List[Text]:
        raise NotImplementedError

    @abstractmethod
    async def query(self, queries: List[Query]) -> List[QueryResult]:
        raise NotImplementedError

    @abstractmethod
    async def delete(
        self,
        ids: Optional[List[Text]] = None,
        filter: Optional[DocumentMetadataFilter] = None,
        delete_all: Optional[bool] = None,
    ) -> bool:
        raise NotImplementedError
