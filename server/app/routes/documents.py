"""Document routes (Member 2). The real work happens in document_processing/upload_service.py."""
from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import Settings
from app.core.dependencies import get_embedder, get_registry, get_settings, get_vector_store
from app.core.registry import DocumentRegistry
from app.document_processing.upload_service import handle_upload
from app.schemas import DocumentListResponse, DocumentOut, ProcessingSummary, UploadResponse

router = APIRouter()


@router.post("/documents/upload", response_model=UploadResponse)
def upload_document(
    file: UploadFile = File(...),  # the multipart form field must be named "file"
    settings: Settings = Depends(get_settings),
    registry: DocumentRegistry = Depends(get_registry),
    embedder=Depends(get_embedder),
    store=Depends(get_vector_store),
) -> UploadResponse:
    # This is a plain `def` (not async) so FastAPI runs it in a worker thread; PDF parsing and
    # embedding are slow and must not block the server's event loop.
    record = handle_upload(
        stream=file.file,
        filename=file.filename,
        settings=settings,
        registry=registry,
        embedder=embedder,
        store=store,
    )
    return UploadResponse(
        document_id=record["document_id"],
        filename=record["filename"],
        status=record["status"],
        message=record["message"],
        processing_summary=ProcessingSummary(
            page_count=record["page_count"],
            pages_with_text=record["pages_with_text"],
            chunk_count=record["chunk_count"],
            size_bytes=record["size_bytes"],
        ),
    )


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(registry: DocumentRegistry = Depends(get_registry)) -> DocumentListResponse:
    return DocumentListResponse(documents=[DocumentOut(**d) for d in registry.list()])
