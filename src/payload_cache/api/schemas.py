from uuid import UUID

from pydantic import BaseModel, model_validator


class PayloadRequest(BaseModel):
    list_1: list[str]
    list_2: list[str]

    @model_validator(mode="after")
    def validate_lengths(self) -> "PayloadRequest":
        if len(self.list_1) != len(self.list_2):
            raise ValueError("list_1 and list_2 must have the same length")
        return self


class PayloadCreated(BaseModel):
    id: UUID


class PayloadResponse(BaseModel):
    output: str
