from pydantic import BaseModel, ConfigDict


class ApiError(BaseModel):
    detail: str

    model_config = ConfigDict(frozen=True)
