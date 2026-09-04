from hashlib import sha256
from typing import Protocol

from app.core.config import Settings
from app.models.generation import (
    GenerationCreate,
    GenerationRead,
    GenerationUsage,
)


class GenerationService(Protocol):
    """Keep API code independent from any specific LLM SDK or provider."""

    async def generate(self, request: GenerationCreate) -> GenerationRead:
        """Create one provider-neutral text generation from validated input."""
        ...


class DemoGenerationService:
    """Provide keyless, deterministic output for local full-stack development."""

    def __init__(self, model: str) -> None:
        self._model = model

    async def generate(self, request: GenerationCreate) -> GenerationRead:
        """Produce repeatable placeholder text while preserving a real async seam."""
        canonical_request = request.model_dump_json(exclude_none=True)
        generation_hash = sha256(
            f"{self._model}:{canonical_request}".encode()
        ).hexdigest()[:16]

        compact_prompt = " ".join(request.prompt.split())
        prompt_preview = (
            compact_prompt if len(compact_prompt) <= 180 else f"{compact_prompt[:179]}…"
        )
        output = (
            f'Demo response for "{prompt_preview}". '
            "Connect a production GenerationService to replace this placeholder."
        )
        input_characters = len(request.prompt) + len(request.instructions or "")

        return GenerationRead(
            id=f"gen_demo_{generation_hash}",
            provider="demo",
            model=self._model,
            output=output,
            usage=GenerationUsage(
                input_characters=input_characters,
                output_characters=len(output),
            ),
        )


def build_generation_service(settings: Settings) -> GenerationService:
    """Select the configured provider behind a single replaceable factory."""
    if settings.llm_provider == "demo":
        return DemoGenerationService(model=settings.llm_model)

    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
