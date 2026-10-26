import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from payload_cache.cli import CLISettings, run


def test_cli_repeat_and_output(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "POST":
            assert request.url.path == "/payload"
            assert json.loads(request.content) == {
                "list_1": ["hello"], "list_2": ["world"]
            }
            return httpx.Response(
                201, json={"id": "550e8400-e29b-41d4-a716-446655440000"}
            )
        assert request.url.path == "/payload/550e8400-e29b-41d4-a716-446655440000"
        return httpx.Response(200, json={"output": "HELLO, WORLD"})

    output = tmp_path / "output.json"
    settings = CLISettings(_cli_parse_args=[
        "--host", "http://testserver", "-r", "3", "-j",
        '{"list_1":["hello"],"list_2":["world"]}', "-o", str(output)
    ])
    with httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://testserver"
    ) as client:
        result = run(settings, client)
    assert isinstance(result, list)
    assert len(requests) == 6
    assert len({item["id"] for item in result}) == 1
    assert json.loads(output.read_text(encoding="utf-8")) == result


def test_cli_reads_file_and_stdout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "input.json"
    source.write_text('{"list_1":[],"list_2":[]}', encoding="utf-8")
    settings = CLISettings(_cli_parse_args=["-i", str(source)])

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(
                201, json={"id": "550e8400-e29b-41d4-a716-446655440000"}
            )
        return httpx.Response(200, json={"output": ""})

    with httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://testserver"
    ) as client:
        run(settings, client)
    assert json.loads(capsys.readouterr().out)["output"] == ""


def test_cli_validates_options_and_payload() -> None:
    with pytest.raises(ValidationError):
        CLISettings(_cli_parse_args=["-r", "0", "-j", "{}"])
    with pytest.raises(ValidationError):
        CLISettings(_cli_parse_args=["-j", "{}", "-i", "file.json"])
    with pytest.raises(ValidationError):
        CLISettings(_cli_parse_args=[])
    with pytest.raises(ValidationError):
        run(CLISettings(_cli_parse_args=[
            "-j", '{"list_1":["hello"],"list_2":[]}'
        ]))
