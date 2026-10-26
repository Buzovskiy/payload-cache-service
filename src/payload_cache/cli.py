"""CLI client for exercising the payload cache API."""

import json
import sys
from pathlib import Path
from typing import Any

import httpx
from pydantic import AliasChoices, Field, HttpUrl, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from payload_cache.api.schemas import PayloadCreated, PayloadRequest, PayloadResponse


class CLISettings(BaseSettings):
    """Validate CLI arguments using Pydantic Settings."""

    model_config = SettingsConfigDict(
        cli_parse_args=True, cli_prog_name="cache-cli", extra="ignore"
    )

    host: HttpUrl = HttpUrl("http://127.0.0.1:8005")
    repeat: int = Field(default=1, ge=1, validation_alias=AliasChoices("repeat", "r"))
    input_file: str | None = Field(
        default=None, validation_alias=AliasChoices("input", "i")
    )
    json_input: str | None = Field(
        default=None, validation_alias=AliasChoices("json", "j")
    )
    output_file: str = Field(
        default="-", validation_alias=AliasChoices("output", "o")
    )

    @model_validator(mode="after")
    def validate_input_source(self) -> "CLISettings":
        if (self.input_file is None) == (self.json_input is None):
            raise ValueError("Provide exactly one of --input or --json")
        return self


def load_request(settings: CLISettings) -> PayloadRequest:
    if settings.json_input is not None:
        raw = settings.json_input
    elif settings.input_file == "-":
        raw = sys.stdin.read()
    else:
        assert settings.input_file is not None
        raw = Path(settings.input_file).read_text(encoding="utf-8")
    return PayloadRequest.model_validate_json(raw)


def run(settings: CLISettings, client: httpx.Client | None = None) -> object:
    payload = load_request(settings)
    if client is None:
        with httpx.Client(base_url=str(settings.host).rstrip("/"), timeout=10) as http:
            results = execute(payload, settings.repeat, http)
    else:
        results = execute(payload, settings.repeat, client)

    result: object = results[0] if settings.repeat == 1 else results
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if settings.output_file == "-":
        sys.stdout.write(rendered)
    else:
        Path(settings.output_file).write_text(rendered, encoding="utf-8")
    return result


def execute(
    payload: PayloadRequest, repeat: int, client: httpx.Client
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for _ in range(repeat):
        response = client.post("/payload", json=payload.model_dump(mode="json"))
        response.raise_for_status()
        created = PayloadCreated.model_validate(response.json())
        response = client.get(f"/payload/{created.id}")
        response.raise_for_status()
        content = PayloadResponse.model_validate(response.json())
        results.append({"id": str(created.id), "output": content.output})
    return results


def main() -> int:
    try:
        run(CLISettings())
    except (OSError, ValueError, ValidationError, httpx.HTTPError) as exc:
        print(f"cache-cli: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
