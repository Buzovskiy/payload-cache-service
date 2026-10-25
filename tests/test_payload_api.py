from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from payload_cache.api.routes.payload import get_payload_service
from payload_cache.main import create_app
from test_payload_service import build_service


def test_payload_endpoints_and_validation(tmp_path: Path) -> None:
    service, _, _ = build_service(tmp_path)
    app = create_app()
    app.dependency_overrides[get_payload_service] = lambda: service
    with TestClient(app) as client:
        data = {"list_1": ["first", "second"], "list_2": ["other", "another"]}
        response = client.post("/payload", json=data)
        assert response.status_code == 201
        payload_id = UUID(response.json()["id"])
        assert client.post("/payload", json=data).json()["id"] == str(payload_id)
        output = client.get(f"/payload/{payload_id}")
        assert output.status_code == 200
        assert output.json() == {"output": "FIRST, OTHER, SECOND, ANOTHER"}
        assert (
            client.post(
                "/payload", json={"list_1": ["first"], "list_2": []}
            ).status_code
            == 422
        )
        assert client.get(f"/payload/{UUID(int=0)}").status_code == 404
        assert client.get("/payload/not-a-uuid").status_code == 422


def test_missing_file_returns_500(tmp_path: Path) -> None:
    service, _, _ = build_service(tmp_path)
    payload_id = service.create(["a"], ["b"])
    (tmp_path / f"{payload_id}.json").unlink()
    app = create_app()
    app.dependency_overrides[get_payload_service] = lambda: service
    with TestClient(app) as client:
        response = client.get(f"/payload/{payload_id}")
    assert response.status_code == 500
    assert response.json()["detail"] == "Stored payload file is missing"
