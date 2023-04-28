from typing import Text

from .qdrant import QdrantDocumentStore


def get_document_store(collection_name: Text) -> "QdrantDocumentStore":
    return QdrantDocumentStore(collection_name=collection_name)
