"""
router.py — Aggregates all v1 endpoint routers into a single APIRouter.

Adding a new feature (e.g. documents, chat) requires only:
  1. Create app/api/v1/endpoints/your_feature.py
  2. Add one `router.include_router(...)` line here.

main.py never needs to change.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import documents, chat, health

router = APIRouter()

# ------------------------------------------------------------------ #
# Health — always first; no auth required
# ------------------------------------------------------------------ #
router.include_router(
    health.router,
    prefix="/health",
    tags=["health"],
)

# ------------------------------------------------------------------ #
# Documents — upload, list, delete
# ------------------------------------------------------------------ #
router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"],
)

# ------------------------------------------------------------------ #
# Chat — question answering with conversation history
# ------------------------------------------------------------------ #
router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"],
)
