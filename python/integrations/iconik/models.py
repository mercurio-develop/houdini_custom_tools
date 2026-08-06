"""Data models for Iconik upload operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class IconikUploadResult:
    success: bool
    message: str
    asset_id: Optional[str] = None
    file_id: Optional[str] = None
    job_id: Optional[str] = None
    skipped: bool = False
    details: dict[str, Any] = field(default_factory=dict)
