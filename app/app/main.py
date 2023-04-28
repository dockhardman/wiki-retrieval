import openai
import sanic
from pyassorted.datetime import Timer
from sanic.request import Request
from sanic.response import text as PlainTextResponse

from app.config import logger, settings
from app.deps import click_timer, get_document_store
from app.document_store import QdrantDocumentStore


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
        if touch_doc_store is False:
            raise ValueError(
                f'Failed to touch document store: "{doc_store.host}:{doc_store.port}"'
            )

    @app.get("/")
    async def root(request: "Request"):
        return PlainTextResponse("OK")

    # Dependencies injection
    app.ext.add_dependency(Timer, click_timer)
    app.ext.add_dependency(QdrantDocumentStore, get_document_store)

    # Blueprint

    return app


app = create_app()
