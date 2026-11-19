from hashlib import sha256
from typing import Protocol

from app.generation.models import GenerationCreate, GenerationRead, GenerationUsage


class GenerationService(Protocol):
    """Isolate HTTP behavior from provider SDKs and provider-specific responses."""

    provider: str
    model: str

    async def generate(self, request: GenerationCreate) -> GenerationRead: ...


class DemoGenerationService:
    """Provide deterministic local output with no external provider configuration."""

    provider = "demo"

    def __init__(self, model: str) -> None:
        self.model = model

    async def generate(self, request: GenerationCreate) -> GenerationRead:
        canonical_request = request.model_dump_json(exclude_none=True)
        generation_hash = sha256(
            f"{self.model}:{canonical_request}".encode()
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
            provider=self.provider,
            model=self.model,
            output=output,
            usage=GenerationUsage(
                input_characters=input_characters,
                output_characters=len(output),
            ),
        )
