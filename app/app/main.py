import asyncio
import uuid
from dataclasses import asdict
from typing import List, Text, Union

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
from app.schema.api import UpsertCall, UpsertResponse
from app.schema.models import DocumentWithEmbedding
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
            emb_docs: List["DocumentWithEmbedding"] = []
            emb_task = await request.app.dispatch(
                "openai.embedding.text",
                context=dict(texts=[doc.text for doc in upsert_call.documents]),
            )
            emb_task_result: List[
                Union[Exception, List[List[float]]]
            ] = await asyncio.gather(emb_task)
            _embeddings = emb_task_result[0]
            for doc, emb in zip(upsert_call.documents, _embeddings):
                if isinstance(emb, Exception):
                    raise ServerError("Internal Service Error")
                emb_doc = from_dict(
                    data_class=DocumentWithEmbedding,
                    data=dict(embedding=emb, **asdict(doc)),
                )
                if not emb_doc.id:
                    emb_doc.id = str(uuid.uuid4())
                emb_docs.append(emb_doc)

            ids = await doc_store.upsert(documents=emb_docs)
            return JsonResponse(asdict(UpsertResponse(ids=ids)))
        except Exception as e:
            logger.exception(e)
            raise ServerError("Internal Service Error")

    # Dependencies injection
    app.ext.add_dependency(Timer, click_timer)
    app.ext.add_dependency(QdrantDocumentStore, get_document_store)

    # Blueprint

    return app


app = create_app()
