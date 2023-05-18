import datetime
from dataclasses import asdict
from typing import Dict, List, Optional, Text

import qdrant_client
from pyassorted.asyncio import run_func
from qdrant_client.models import models as qdrant_models

from .abc import DocumentStore
from app.config import logger, settings
from app.schema.models import (
    DocumentWithEmbedding,
    DocumentWithScore,
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
                    return True
                except Exception as e:
                    logger.exception(e)
            else:
                logger.exception(e)
        return False

    async def upsert(self, documents: List[DocumentWithEmbedding]) -> List[Text]:
        created_at = datetime.datetime.utcnow().isoformat()
        points: List[qdrant_models.PointStruct] = []
        for doc in documents:
            _point = qdrant_models.PointStruct(
                id=doc.id,
                vector=doc.embedding,
                payload=asdict(doc),
            )
            _point.payload["created_at"] = created_at
            points.append(_point)

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )
        return [d.id for d in documents]

    async def query(self, queries: List[QueryWithEmbedding]) -> List[QueryResult]:
        search_requests = [
            qdrant_models.SearchRequest(
                vector=query.embedding,
                filter=query.filter,
                limit=query.top_k,
                with_payload=True,
                with_vector=False,
            )
            for query in queries
        ]
        results = self.client.search_batch(
            collection_name=self.collection_name,
            requests=search_requests,
        )
        return [
            QueryResult(
                query=query.query,
                results=[
                    DocumentWithScore(
                        id=point.payload.get("id") if point.payload else None,
                        text=point.payload.get("text", ""),
                        metadata=point.payload.get("metadata"),
                        embedding=point.vector,
                        score=point.score,
                    )
                    for point in result
                ],
            )
            for query, result in zip(queries, results)
        ]

    async def delete(
        self,
        ids: Optional[List[Text]] = None,
        filter: Optional[Dict] = None,
        delete_all: Optional[bool] = None,
    ) -> bool:
        if ids is None and filter is None and delete_all is None:
            raise ValueError(
                "Please provide one of the parameters: ids, filter or delete_all."
            )

        if delete_all:
            points_selector = qdrant_models.Filter()
        else:
            points_selector = self._convert_filter(filter, ids)

        response = self.client.delete(
            collection_name=self.collection_name,
            points_selector=points_selector,
        )
        return qdrant_models.UpdateStatus.COMPLETED == response.status
