import asyncio

from app.generation.models import GenerationCreate
from app.generation.service import DemoGenerationService


def test_demo_generation_is_deterministic() -> None:
    service = DemoGenerationService(model="demo-test")
    request = GenerationCreate(
        prompt="Explain retrieval augmented generation.",
        instructions="Keep it concise.",
        temperature=0.3,
    )

    first = asyncio.run(service.generate(request))
    second = asyncio.run(service.generate(request))

    assert first == second
    assert first.id.startswith("gen_demo_")
    assert first.provider == "demo"
    assert first.model == "demo-test"
    assert request.prompt in first.output
    assert first.usage.input_characters == len(request.prompt) + len(
        request.instructions or ""
    )
    assert first.usage.output_characters == len(first.output)
