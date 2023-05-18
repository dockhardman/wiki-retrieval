import asyncio
from dataclasses import asdict
from typing import List, Text

import openai
import sanic
from dacite import from_dict
from openai.openai_object import OpenAIObject
from pyassorted.datetime import Timer
from sanic_ext import openapi
from sanic.exceptions import BadRequest, ServerError
from sanic.request import Request
from sanic.response import text as PlainTextResponse, json as JsonResponse

from app.config import logger, settings
from app.deps import click_timer, get_document_store
from app.document_store import QdrantDocumentStore
from app.schema.api import (
    DeleteCall,
    DeleteResponse,
    QueryCall,
    QueryResponse,
    UpsertCall,
    UpsertResponse,
)
from app.schema.models import QueryWithEmbedding
from app.schema.openai import OpenaiEmbeddingResult


def create_app():
    app = sanic.Sanic(
        name=settings.APP_NAME,
    )

    @app.before_server_start
    async def before_server_start(*_):
        # Set OpenAI credential
        openai.api_key = settings.OPENAI_API_KEY
        logger.debug("Have set OpenAI credential.")
        # Create document store client
        doc_store = QdrantDocumentStore(collection_name=settings.QDRANT_COLLECTION)
        app.ctx.document_store = doc_store
        touch_doc_store = await doc_store.touch()
        if touch_doc_store:
            logger.debug("Connected to document store.")
        else:
            raise ValueError(
                f'Failed to touch document store: "{doc_store.host}:{doc_store.port}"'
            )

    @app.signal("openai.embedding.text")
    async def openai_embedding_text(texts: List[Text], **context) -> List[List[float]]:
        texts = [texts] if isinstance(texts, Text) else texts
        texts = [text.strip() for text in texts]
        emb_res_obj: "OpenAIObject" = await openai.Embedding.acreate(
            input=texts, model="text-embedding-ada-002"
        )
        emb_res: OpenaiEmbeddingResult = emb_res_obj.to_dict_recursive()
        return [emb["embedding"] for emb in emb_res["data"]]

    @app.get("/")
    async def root(request: "Request"):
        return PlainTextResponse("OK")

    @app.post("/upsert")
    @openapi.body(UpsertCall, body_argument="upsert_call")
    async def upsert(request: "Request", doc_store: "QdrantDocumentStore"):
        try:
            upsert_call = from_dict(data_class=UpsertCall, data=request.json)
        except Exception:
            raise BadRequest("Invalid request body")

        if not upsert_call.documents:
            raise BadRequest("Empty documents")

        try:
            # Embedding
            _embeddings = await dispatch_embeddings(
                request=request, texts=[doc.text for doc in upsert_call.documents]
            )
            emb_docs = [
                doc.to_document_with_embedding(embedding=emb)
                for doc, emb in zip(upsert_call.documents, _embeddings)
            ]

            # Upsert
            ids = await doc_store.upsert(documents=emb_docs)
            return JsonResponse(asdict(UpsertResponse(ids=ids)))

        except Exception as e:
            logger.exception(e)
            raise ServerError("Internal Service Error")

    @app.post("/query")
    @app.post("/sub/query", name="sub_query")
    @openapi.body(QueryCall, body_argument="query_call")
    async def query(request: "Request", doc_store: "QdrantDocumentStore"):
        try:
            query_call = from_dict(data_class=QueryCall, data=request.json)
        except Exception:
            raise BadRequest("Invalid request body")

        emb = await request.app.dispatch(
            "openai.embedding.text",
            context=dict(texts=[query.query.strip() for query in query_call.queries]),
        )
        await emb
        embeddings = emb.result()

        emb_queries: List[QueryWithEmbedding] = []
        for query, embedding in zip(query_call.queries, embeddings):
            emb_queries.append(
                from_dict(
                    data_class=QueryWithEmbedding,
                    data=dict(asdict(query), embedding=embedding),
                )
            )

        query_results = await doc_store.query(queries=emb_queries)
        return JsonResponse(asdict(QueryResponse(results=query_results)))

    @app.delete("/delete")
    @openapi.body(DeleteCall, body_argument="delete_call")
    async def delete(request: "Request", doc_store: "QdrantDocumentStore"):
        try:
            delete_call = from_dict(data_class=DeleteCall, data=request.json)
        except Exception:
            raise BadRequest("Invalid request body")

        if not (delete_call.ids or delete_call.filter or delete_call.delete_all):
            raise BadRequest("One of ids, filter, or delete_all is required")

        try:
            success = await doc_store.delete(
                ids=delete_call.ids,
                filter=delete_call.filter,
                delete_all=delete_call.delete_all,
            )
            return JsonResponse(asdict(DeleteResponse(success=success)))
        except Exception as e:
            logger.exception(e)
            raise ServerError("Internal Service Error")

    async def dispatch_embeddings(
        request: "Request", texts: List[Text]
    ) -> List[List[float]]:
        emb_task: "asyncio.Task" = await request.app.dispatch(
            "openai.embedding.text",
            context=dict(texts=texts),
        )
        await emb_task
        embeddings = emb_task.result()
        if isinstance(embeddings, Exception):
            raise ServerError("Internal Service Error")
        return embeddings

    # Dependencies injection
    app.ext.add_dependency(Timer, click_timer)
    app.ext.add_dependency(QdrantDocumentStore, get_document_store)

    # Blueprint

    return app


app = create_app()
