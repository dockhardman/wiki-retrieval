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
from app.schema import api as api_model
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
    @openapi.definition(
        summary="Upsert documents",
        description="Upsert documents to document store",
        body=api_model.UpsertCall,
        response=api_model.UpsertResponse,
    )
    async def upsert(request: "Request", doc_store: "QdrantDocumentStore"):
        try:
            upsert_call = from_dict(data_class=api_model.UpsertCall, data=request.json)
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
                doc.with_embedding(embedding=emb)
                for doc, emb in zip(upsert_call.documents, _embeddings)
            ]

            # Upsert
            ids = await doc_store.upsert(documents=emb_docs)
            return JsonResponse(asdict(api_model.UpsertResponse(ids=ids)))

        except Exception as e:
            logger.exception(e)
            raise ServerError("Internal Service Error")

    @app.post("/query")
    @app.post("/sub/query", name="sub_query")
    @openapi.definition(
        summary="Query documents",
        description="Query documents from document store",
        body=api_model.QueryCall,
        response=api_model.QueryResponse,
    )
    async def query(request: "Request", doc_store: "QdrantDocumentStore"):
        try:
            query_call = from_dict(data_class=api_model.QueryCall, data=request.json)
        except Exception:
            raise BadRequest("Invalid request body")

        try:
            # Embedding
            _embeddings = await dispatch_embeddings(
                request=request, texts=[query.query for query in query_call.queries]
            )
            emb_queries = [
                doc.with_embedding(embedding=emb)
                for doc, emb in zip(query_call.queries, _embeddings)
            ]

            query_results = await doc_store.query(queries=emb_queries)
            return JsonResponse(asdict(api_model.QueryResponse(results=query_results)))

        except Exception as e:
            logger.exception(e)
            raise ServerError("Internal Service Error")

    @app.delete("/delete")
    @openapi.definition(
        summary="Delete documents",
        description="Delete documents from document store",
        body=api_model.DeleteCall,
        response=api_model.DeleteResponse,
    )
    async def delete(request: "Request", doc_store: "QdrantDocumentStore"):
        try:
            delete_call = from_dict(data_class=api_model.DeleteCall, data=request.json)
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
            return JsonResponse(asdict(api_model.DeleteResponse(success=success)))

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
