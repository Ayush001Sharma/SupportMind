"""
test_document_processor.py — Unit tests for PDF, DOCX, and TXT processing.

All tests write temporary files to tmp_path (pytest's built-in temp dir)
so no production storage is touched. No Ollama or ChromaDB calls happen here.
"""

import io
import uuid
from pathlib import Path

import pytest

from app.core.exceptions import DocumentNotFoundError, DocumentProcessingError


class TestTxtProcessing:
    """Tests for plain text document extraction."""

    def test_txt_extracts_text(self, tmp_path, sample_txt_bytes):
        from app.services.document_processor import process_document

        doc_id = str(uuid.uuid4())
        file_path = tmp_path / f"{doc_id}_support_hours.txt"
        file_path.write_bytes(sample_txt_bytes)

        result = process_document(file_path)

        assert result.document_type == "txt"
        assert result.total_pages >= 1
        assert len(result.pages[0].text) > 0
        assert "support" in result.pages[0].text.lower()

    def test_txt_preserves_filename(self, tmp_path, sample_txt_bytes):
        from app.services.document_processor import process_document

        doc_id = str(uuid.uuid4())
        file_path = tmp_path / f"{doc_id}_myfile.txt"
        file_path.write_bytes(sample_txt_bytes)

        result = process_document(file_path)

        assert result.filename == "myfile.txt"

    def test_missing_file_raises_not_found(self, tmp_path):
        from app.services.document_processor import process_document

        missing = tmp_path / "ghost.txt"
        with pytest.raises(DocumentNotFoundError):
            process_document(missing)

    def test_empty_txt_raises_processing_error(self, tmp_path):
        from app.services.document_processor import process_document

        doc_id = str(uuid.uuid4())
        file_path = tmp_path / f"{doc_id}_empty.txt"
        # Write only whitespace — should be empty after preprocessing
        file_path.write_bytes(b"   \n\n   ")

        with pytest.raises(DocumentProcessingError):
            process_document(file_path)


class TestPdfProcessing:
    """Tests for PDF document extraction."""

    @pytest.mark.parametrize("mock_empty", [False])
    def test_pdf_is_processed(self, tmp_path, minimal_pdf_bytes, mock_empty):
        from app.services.document_processor import process_document
        from unittest.mock import patch

        doc_id = str(uuid.uuid4())
        file_path = tmp_path / f"{doc_id}_report.pdf"
        file_path.write_bytes(minimal_pdf_bytes)

        with patch("app.services.document_processor.is_empty_page", return_value=mock_empty):
            result = process_document(file_path)

        assert result.document_type == "pdf"
        assert result.total_pages >= 1

    def test_corrupted_pdf_raises_processing_error(self, tmp_path):
        from app.services.document_processor import process_document

        doc_id = str(uuid.uuid4())
        file_path = tmp_path / f"{doc_id}_corrupt.pdf"
        file_path.write_bytes(b"NOT A PDF AT ALL")

        with pytest.raises(DocumentProcessingError):
            process_document(file_path)

    def test_pdf_page_metadata_populated(self, tmp_path, minimal_pdf_bytes):
        from app.services.document_processor import process_document
        from unittest.mock import patch

        doc_id = str(uuid.uuid4())
        file_path = tmp_path / f"{doc_id}_doc.pdf"
        file_path.write_bytes(minimal_pdf_bytes)

        with patch("app.services.document_processor.is_empty_page", return_value=False):
            result = process_document(file_path)

        for page in result.pages:
            assert page.metadata.document_type == "pdf"
            assert page.page_number >= 1


class TestDocxProcessing:
    """Tests for DOCX document extraction."""

    def test_docx_is_processed(self, tmp_path, minimal_docx_bytes):
        from app.services.document_processor import process_document
        from unittest.mock import patch

        doc_id = str(uuid.uuid4())
        file_path = tmp_path / f"{doc_id}_letter.docx"
        file_path.write_bytes(minimal_docx_bytes)

        with patch("app.services.document_processor.is_empty_page", return_value=False):
            result = process_document(file_path)

        assert result.document_type == "docx"
        assert result.total_pages >= 1
        assert "DOCX" in result.pages[0].text or "test document" in result.pages[0].text.lower()

    def test_corrupted_docx_raises_processing_error(self, tmp_path):
        from app.services.document_processor import process_document

        doc_id = str(uuid.uuid4())
        file_path = tmp_path / f"{doc_id}_corrupt.docx"
        file_path.write_bytes(b"NOT A DOCX")

        with pytest.raises(DocumentProcessingError):
            process_document(file_path)

    def test_unsupported_extension_raises(self, tmp_path):
        from app.services.document_processor import process_document

        doc_id = str(uuid.uuid4())
        file_path = tmp_path / f"{doc_id}_data.csv"
        file_path.write_text("a,b,c", encoding="utf-8")

        from app.core.exceptions import UnsupportedFileTypeError
        with pytest.raises(UnsupportedFileTypeError):
            process_document(file_path)
