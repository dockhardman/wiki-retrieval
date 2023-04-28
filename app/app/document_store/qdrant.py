from typing import Dict, List, Optional, Text

import qdrant_client
from pyassorted.asyncio import run_func
from qdrant_client.models import models as qdrant_models

from .abc import DocumentStore
from app.config import logger, settings
from app.schema.models import (
    Document,
    DocumentChunk,
    DocumentMetadataFilter,
    Query,
    QueryResult,
    QueryWithEmbedding,
)


class QdrantDocumentStore(DocumentStore):
    def __init__(
        self,
        collection_name: Optional[str] = None,
        vector_size: int = 1536,
        distance: str = "Cosine",
    ):
        self._host = settings.QDRANT_URL
        self._port = int(settings.QDRANT_PORT)
        self._grpc_port = int(settings.QDRANT_GRPC_PORT)
        self.vector_size = int(vector_size)
        self.distance = distance

        self.client = qdrant_client.QdrantClient(
            url=self._host,
            port=self._port,
            grpc_port=self._grpc_port,
            api_key=settings.QDRANT_API_KEY,
            prefer_grpc=True,
            timeout=10,
        )
        self.collection_name = collection_name

    @property
    def host(self) -> Text:
        return self._host

    @property
    def port(self) -> Text:
        return self._port

    async def touch(self) -> bool:
        try:
            await run_func(self.client.get_collection, self.collection_name)
            return True
        except Exception as e:
            if "Not found: Collection" in str(e):
                logger.info(f"Create collection: {self.collection_name}")
                try:
                    await run_func(
                        self.client.create_collection,
                        self.collection_name,
                        vectors_config=qdrant_models.VectorParams(
                            size=self.vector_size,
                            distance=self.distance,
                        ),
                    )
                except Exception as e:
                    logger.exception(e)
            else:
                logger.exception(e)
        return False

    async def upsert(
        self, documents: List[Document], chunk_token_size: Optional[int] = None
    ) -> List[Text]:
        raise NotImplementedError

    async def _upsert(self, chunks: Dict[str, List[DocumentChunk]]) -> List[Text]:
        raise NotImplementedError

    async def query(self, queries: List[Query]) -> List[QueryResult]:
        raise NotImplementedError

    async def _query(self, queries: List[QueryWithEmbedding]) -> List[QueryResult]:
        raise NotImplementedError

    async def delete(
        self,
        ids: Optional[List[Text]] = None,
        filter: Optional[DocumentMetadataFilter] = None,
        delete_all: Optional[bool] = None,
    ) -> bool:
        raise NotImplementedError