"""CLI stdin and network-failure regression tests."""

import io
import json
import sys

import httpx
import pytest

from payload_cache.cli import CLISettings, main, run


def test_cli_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["cache-cli", "--input", "-"])
    monkeypatch.setattr(
        sys, "stdin", io.StringIO('{"list_1":["one"],"list_2":["two"]}')
    )
    settings = CLISettings()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            assert json.loads(request.content)["list_1"] == ["one"]
            return httpx.Response(
                201, json={"id": "550e8400-e29b-41d4-a716-446655440000"}
            )
        return httpx.Response(200, json={"output": "ONE, TWO"})

    with httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://testserver"
    ) as client:
        run(settings, client)
    assert json.loads(capsys.readouterr().out)["output"] == "ONE, TWO"


def test_cli_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys, "argv", ["cache-cli", "--json", '{"list_1":[],"list_2":[]}']
    )
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(503)),
        base_url="http://testserver",
    ) as client:
        with pytest.raises(httpx.HTTPStatusError):
            run(CLISettings(), client)


def test_cli_main_exits_nonzero_on_invalid_input(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        sys, "argv", ["cache-cli", "--json", '{"list_1":["a"],"list_2":[]}']
    )
    assert main() == 1
    assert "cache-cli:" in capsys.readouterr().err
