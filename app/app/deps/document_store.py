from sanic.request import Request

from app.document_store import QdrantDocumentStore


def get_document_store(request: Request) -> "QdrantDocumentStore":
    return request.app.ctx.document_store
