"""
test_chunking_service.py — Unit tests for the ChunkingService.

Verifies that ProcessedDocument objects are correctly split into
LangChain Documents with accurate metadata and deterministic IDs.
No external I/O occurs.
"""

import pytest
from langchain_core.documents import Document


class TestChunkDocument:
    """Tests for chunk_document() correctness."""

    def test_returns_list_of_documents(self, processed_document, settings):
        from app.services.chunking_service import chunk_document

        chunks = chunk_document(processed_document, settings)

        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(c, Document) for c in chunks)

    def test_chunk_preserves_filename_metadata(self, processed_document, settings):
        from app.services.chunking_service import chunk_document

        chunks = chunk_document(processed_document, settings)

        for chunk in chunks:
            assert chunk.metadata["filename"] == processed_document.filename

    def test_chunk_preserves_page_number_metadata(self, processed_document, settings):
        from app.services.chunking_service import chunk_document

        chunks = chunk_document(processed_document, settings)

        for chunk in chunks:
            assert "page_number" in chunk.metadata
            assert chunk.metadata["page_number"] >= 1

    def test_chunk_preserves_doc_type_metadata(self, processed_document, settings):
        from app.services.chunking_service import chunk_document

        chunks = chunk_document(processed_document, settings)

        for chunk in chunks:
            assert chunk.metadata["doc_type"] == processed_document.document_type

    def test_chunk_ids_are_deterministic(self, processed_document, settings):
        """Running chunk_document twice with the same input must produce identical IDs."""
        from app.services.chunking_service import chunk_document

        chunks_a = chunk_document(processed_document, settings)
        chunks_b = chunk_document(processed_document, settings)

        ids_a = [c.id for c in chunks_a]
        ids_b = [c.id for c in chunks_b]

        assert ids_a == ids_b

    def test_chunk_ids_are_unique_within_document(self, processed_document, settings):
        from app.services.chunking_service import chunk_document

        chunks = chunk_document(processed_document, settings)
        ids = [c.id for c in chunks]

        assert len(ids) == len(set(ids))

    def test_empty_document_returns_empty_list(self, settings):
        """A document with no pages should produce zero chunks."""
        from app.schemas.processing import ProcessedDocument
        from app.services.chunking_service import chunk_document

        empty_doc = ProcessedDocument(
            document_id="empty-doc-id",
            filename="empty.txt",
            document_type="txt",
            upload_timestamp="2026-07-06T00:00:00Z",
            total_pages=0,
            pages=[],
        )

        chunks = chunk_document(empty_doc, settings)
        assert chunks == []

    def test_chunk_content_is_non_empty(self, processed_document, settings):
        from app.services.chunking_service import chunk_document

        chunks = chunk_document(processed_document, settings)

        for chunk in chunks:
            assert len(chunk.page_content.strip()) > 0
