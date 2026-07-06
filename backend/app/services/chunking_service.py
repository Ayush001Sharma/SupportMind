"""
chunking_service.py — Document chunking layer.

This service is solely responsible for splitting structured text into smaller,
semantically meaningful chunks suitable for embedding, while preserving
all associated metadata. It operates purely in memory.
"""

import hashlib
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import Settings
from app.schemas.processing import ProcessedDocument


def chunk_document(processed_doc: ProcessedDocument, settings: Settings) -> List[Document]:
    """
    Split a ProcessedDocument into a list of LangChain Document chunks.

    Parameters
    ----------
    processed_doc : ProcessedDocument
        The structured document output from the document_processor.
    settings : Settings
        Application configuration containing chunk sizes and overlaps.

    Returns
    -------
    List[Document]
        A list of LangChain Document objects with attached metadata and a
        deterministic SHA-256 hash ID.
    """
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    documents_to_index: List[Document] = []

    for page in processed_doc.pages:
        chunks = splitter.split_text(page.text)

        for chunk_idx, chunk_text in enumerate(chunks):
            # Deterministic chunk ID mapping to filename, page, and chunk index
            chunk_id_str = f"{processed_doc.document_id}_{page.page_number}_{chunk_idx}"
            chunk_uuid = hashlib.sha256(chunk_id_str.encode("utf-8")).hexdigest()

            doc = Document(
                page_content=chunk_text,
                metadata={
                    "filename": processed_doc.filename,
                    "page_number": page.page_number,
                    "chunk_id": chunk_idx,
                    "upload_timestamp": processed_doc.upload_timestamp,
                    "doc_type": processed_doc.document_type,
                },
                id=chunk_uuid,
            )
            documents_to_index.append(doc)

    return documents_to_index
