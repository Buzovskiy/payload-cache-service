import json
import os
import tempfile
from pathlib import Path


class PayloadFileStorage:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def write(self, filename: str, output: str) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.directory / filename
        temporary: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.directory,
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary = stream.name
                json.dump({"output": output}, stream, ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                Path(temporary).unlink(missing_ok=True)

    def read(self, filename: str) -> str:
        with (self.directory / filename).open(encoding="utf-8") as stream:
            data = json.load(stream)
        result = data["output"]
        if not isinstance(result, str):
            raise ValueError("Stored payload has invalid output")
        return result

    def delete(self, filename: str) -> None:
        (self.directory / filename).unlink(missing_ok=True)
