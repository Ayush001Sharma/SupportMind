"""
documents.py — Document management endpoints.

POST /api/v1/documents/upload  — Upload and save a document (Phase 2) ✅
GET  /api/v1/documents/        — List indexed documents         (Phase 3 stub)
DELETE /api/v1/documents/{id}  — Delete a document             (Phase 3 stub)

The upload endpoint is a thin router layer:
  1. Receive the multipart file from the client.
  2. Delegate all business logic to document_service.upload_document().
  3. Return the DocumentUploadResponse or let the global exception handlers
     in main.py translate any SupportMindError into the appropriate 4xx.

No validation, no I/O, no exception handling lives here.
"""

from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import JSONResponse

from app.api.dependencies import ChromaCollectionDep, EmbeddingsDep, SettingsDep
from app.core.config import Settings
from app.schemas.documents import DocumentUploadResponse
from app.services import document_service

router = APIRouter()


# ------------------------------------------------------------------ #
# POST /upload
# ------------------------------------------------------------------ #


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description=(
        "Upload a PDF, DOCX, or TXT file. The file is validated and saved to "
        "the configured upload directory. Text extraction and ChromaDB indexing "
        "happen in Phase 3. Returns document metadata with status='uploaded'."
    ),
    responses={
        201: {"description": "File accepted and saved successfully"},
        413: {"description": "File exceeds the configured size limit"},
        415: {"description": "File type is not supported (PDF, DOCX, TXT only)"},
    },
)
async def upload_document(
    settings: SettingsDep,
    collection: ChromaCollectionDep,
    embeddings_client: EmbeddingsDep,
    file: Annotated[
        UploadFile,
        File(description="The document to upload. Accepted types: PDF, DOCX, TXT."),
    ],
) -> DocumentUploadResponse:
    """
    Receive a multipart file upload, validate it, and persist it to disk.
    Then extract text, chunk it, and index it into ChromaDB.
    """
    from app.services import ingestion_service

    return await ingestion_service.ingest_document(
        file=file,
        settings=settings,
        collection=collection,
        embeddings_client=embeddings_client,
    )


# ------------------------------------------------------------------ #
# GET / — list documents (Phase 3 stub)
# ------------------------------------------------------------------ #


@router.get(
    "/",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="List indexed documents",
    description="Returns all documents currently indexed in ChromaDB. Implemented in Phase 3.",
)
async def list_documents() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={"detail": "Document listing will be implemented in Phase 3."},
    )


# ------------------------------------------------------------------ #
# DELETE /{doc_id} — delete document (Phase 3 stub)
# ------------------------------------------------------------------ #


@router.delete(
    "/{doc_id}",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Delete a document",
    description=(
        "Removes a document from disk and deletes its chunks from ChromaDB. "
        "Implemented in Phase 3."
    ),
)
async def delete_document(doc_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={"detail": f"Delete for doc_id='{doc_id}' will be implemented in Phase 3."},
    )
