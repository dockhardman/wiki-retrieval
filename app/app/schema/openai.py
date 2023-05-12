from typing import Any, List, Optional, Text, TypedDict


class OpenaiCompletionUsage(TypedDict):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int


class OpenaiEmbeddingUsage(TypedDict):
    prompt_tokens: int
    total_tokens: int


class OpenaiCompletionChoice(TypedDict):
    finish_reason: Text
    index: int
    logprobs: Optional[Any]
    text: Text


class OpenaiEmbedding(TypedDict):
    object: Text
    index: int
    embedding: List[float]


class OpenaiCompletionResult(TypedDict):
    choices: List[OpenaiCompletionChoice]
    created: int
    id: Text
    model: Text
    object: Text
    usage: OpenaiCompletionUsage


class OpenaiEmbeddingResult(TypedDict):
    data: List[OpenaiEmbedding]
    model: Text
    object: Text
    usage: OpenaiEmbeddingUsage
