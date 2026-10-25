from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from payload_cache.api.schemas import PayloadCreated, PayloadRequest, PayloadResponse
from payload_cache.core.config import get_settings
from payload_cache.db.session import get_db
from payload_cache.repositories.payload_repository import PayloadRepository
from payload_cache.repositories.transformation_repository import (
    TransformationRepository,
)
from payload_cache.services.payload_service import (
    PayloadFileMissingError,
    PayloadNotFoundError,
    PayloadService,
)
from payload_cache.services.transformation_service import TransformationService
from payload_cache.storage.file_storage import PayloadFileStorage

router = APIRouter(prefix="/payload", tags=["payload"])


def get_payload_service(db: Session = Depends(get_db)) -> PayloadService:
    settings = get_settings()
    return PayloadService(
        repository=PayloadRepository(db),
        transformation_service=TransformationService(TransformationRepository(db)),
        storage=PayloadFileStorage(settings.payload_directory),
    )


@router.post("", response_model=PayloadCreated, status_code=status.HTTP_201_CREATED)
def create_payload(
    request: PayloadRequest,
    service: PayloadService = Depends(get_payload_service),
) -> PayloadCreated:
    return PayloadCreated(id=service.create(request.list_1, request.list_2))


@router.get("/{payload_id}", response_model=PayloadResponse)
def read_payload(
    payload_id: UUID,
    service: PayloadService = Depends(get_payload_service),
) -> PayloadResponse:
    try:
        return PayloadResponse(output=service.get(payload_id))
    except PayloadNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Payload not found") from exc
    except PayloadFileMissingError as exc:
        raise HTTPException(
            status_code=500, detail="Stored payload file is missing"
        ) from exc
