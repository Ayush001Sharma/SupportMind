"""
services package — business logic, decoupled from HTTP transport.

Service modules (document_processor, vector_store, llm_service) will be
added here in Phases 2 and 3. Each service is a plain Python class/module
with no FastAPI imports, making it independently testable.
"""
