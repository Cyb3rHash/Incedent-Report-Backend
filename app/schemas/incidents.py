from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.incident import IncidentSeverity, IncidentStatus


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Short incident title.")
    description: Optional[str] = Field(None, description="Detailed description of the incident.")
    severity: IncidentSeverity = Field(..., description="Incident severity.")
    status: IncidentStatus = Field(IncidentStatus.open, description="Initial incident status.")


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Short incident title.")
    description: Optional[str] = Field(None, description="Detailed description of the incident.")
    severity: Optional[IncidentSeverity] = Field(None, description="Incident severity.")
    status: Optional[IncidentStatus] = Field(None, description="Incident status.")


class IncidentRead(BaseModel):
    id: uuid.UUID = Field(..., description="Incident UUID.")
    title: str = Field(..., description="Short incident title.")
    description: Optional[str] = Field(None, description="Detailed description of the incident.")
    severity: IncidentSeverity = Field(..., description="Incident severity.")
    status: IncidentStatus = Field(..., description="Incident status.")
    created_at: datetime = Field(..., description="Server-generated creation timestamp (UTC).")
    updated_at: datetime = Field(..., description="Server-generated update timestamp (UTC).")

    model_config = {"from_attributes": True}


class IncidentListResponse(BaseModel):
    items: list[IncidentRead] = Field(..., description="List of incidents.")
    total: int = Field(..., ge=0, description="Total incidents matching query (before pagination).")
    limit: int = Field(..., ge=1, le=200, description="Page size.")
    offset: int = Field(..., ge=0, description="Page offset.")
