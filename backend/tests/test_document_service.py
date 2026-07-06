"""
test_document_service.py — Unit tests for upload validation.

Validation logic lives inline in document_service.upload_document().
We test it via the HTTP endpoint using a mocked TestClient.
"""

import io
import pytest


def _make_file_tuple(filename: str, content: bytes, content_type: str):
    """Build the files dict for requests multipart upload."""
    return ("file", (filename, io.BytesIO(content), content_type))


class TestUploadValidation:
    """Integration tests verifying upload validation through the HTTP layer."""

    def test_valid_txt_upload_succeeds(self, test_client, tmp_path, settings, monkeypatch):
        """A valid TXT file should return 200 with upload metadata."""
        # Redirect upload dir to tmp so no real disk write happens in /storage
        monkeypatch.setattr(settings, "upload_dir", str(tmp_path))

        response = test_client.post(
            "/api/v1/documents/upload",
            files={"file": ("notes.txt", io.BytesIO(b"Support is available Monday through Friday 9-5."), "text/plain")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["document_type"] == "txt"
        assert data["status"] == "indexed"
        assert "document_id" in data

    def test_unsupported_mime_type_returns_415(self, test_client):
        """An image file should return 415 Unsupported Media Type."""
        response = test_client.post(
            "/api/v1/documents/upload",
            files={"file": ("photo.png", io.BytesIO(b"\x89PNG"), "image/png")},
        )
        assert response.status_code == 415

    def test_unsupported_extension_returns_415(self, test_client):
        """A CSV with text/plain MIME should be rejected by extension check."""
        response = test_client.post(
            "/api/v1/documents/upload",
            files={"file": ("data.csv", io.BytesIO(b"a,b,c"), "text/plain")},
        )
        assert response.status_code == 415

    def test_file_too_large_returns_413(self, test_client, settings):
        """A file exceeding the size limit should return 413."""
        big_content = b"A" * (settings.max_upload_size_bytes + 1)
        response = test_client.post(
            "/api/v1/documents/upload",
            files={"file": ("huge.pdf", io.BytesIO(big_content), "application/pdf")},
        )
        assert response.status_code == 413

    def test_error_response_has_error_envelope(self, test_client):
        """Error responses should use the standard {error: {code, message}} structure."""
        response = test_client.post(
            "/api/v1/documents/upload",
            files={"file": ("bad.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
        )
        assert response.status_code == 415
        body = response.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]
