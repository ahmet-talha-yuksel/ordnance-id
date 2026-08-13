"""Define the provider-neutral model gateway contract."""

from collections.abc import Sequence
from typing import Protocol, TypedDict, TypeVar

from pydantic import BaseModel


class Message(TypedDict):
    """Represent one provider-neutral chat message."""

    role: str
    content: str


class ImageInput(TypedDict):
    """Represent a base64-encoded image and its MIME media type."""

    data: str
    media_type: str


SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMProvider(Protocol):
    """Describe operations every model provider must implement."""

    async def complete(
        self,
        messages: Sequence[Message],
        *,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        """Return an unstructured text completion."""
        ...

    async def complete_structured(
        self,
        messages: Sequence[Message],
        schema: type[SchemaT],
        *,
        images: Sequence[ImageInput] | None = None,
    ) -> SchemaT:
        """Return a completion validated against the supplied Pydantic schema."""
        ...

