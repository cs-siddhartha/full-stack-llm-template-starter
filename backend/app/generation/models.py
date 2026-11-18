from pydantic import BaseModel, ConfigDict, Field, field_validator


class GenerationCreate(BaseModel):
    prompt: str = Field(min_length=1, max_length=4_000)
    instructions: str | None = Field(default=None, max_length=2_000)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)

    model_config = ConfigDict(extra="forbid")

    @field_validator("prompt")
    @classmethod
    def require_meaningful_prompt(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("prompt must contain non-whitespace characters")
        return normalized

    @field_validator("instructions")
    @classmethod
    def normalize_instructions(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class GenerationUsage(BaseModel):
    input_characters: int = Field(ge=0)
    output_characters: int = Field(ge=0)

    model_config = ConfigDict(frozen=True)


class GenerationRead(BaseModel):
    id: str
    provider: str
    model: str
    output: str
    usage: GenerationUsage

    model_config = ConfigDict(frozen=True)
