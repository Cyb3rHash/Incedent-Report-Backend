from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.flows.incidents_flow import IncidentsFlow
from app.schemas.incidents import IncidentCreate, IncidentListResponse, IncidentRead, IncidentUpdate
from app.services.incidents_service import IncidentsService

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


def _get_flow(
    session: AsyncSession,
) -> IncidentsFlow:
    service = IncidentsService(session)
    return IncidentsFlow(service)


@router.post(
    "",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an incident",
    description="Create a new incident with title, optional description, severity, and status.",
    operation_id="createIncident",
)
async def create_incident(
    payload: IncidentCreate,
    session: Annotated[AsyncSession, Depends(lambda: None)] = None,  # overridden below
) -> IncidentRead:
    """Create an incident.

    Returns the created incident including server-generated id and timestamps.
    """
    # The lambda placeholder is replaced in `create_app` dependency overrides to keep typing clean.
    flow = _get_flow(session)
    return await flow.create(payload)


@router.get(
    "",
    response_model=IncidentListResponse,
    summary="List incidents",
    description="Fetch a paginated list of incidents sorted by newest first.",
    operation_id="listIncidents",
)
async def list_incidents(
    limit: int = Query(20, ge=1, le=200, description="Max number of items to return."),
    offset: int = Query(0, ge=0, description="Number of items to skip."),
    session: Annotated[AsyncSession, Depends(lambda: None)] = None,  # overridden below
) -> IncidentListResponse:
    """List incidents with pagination."""
    flow = _get_flow(session)
    return await flow.list(limit=limit, offset=offset)


@router.get(
    "/{incident_id}",
    response_model=IncidentRead,
    summary="Get an incident by id",
    description="Fetch a single incident by its UUID.",
    operation_id="getIncident",
)
async def get_incident(
    incident_id: uuid.UUID = Path(..., description="Incident UUID."),
    session: Annotated[AsyncSession, Depends(lambda: None)] = None,  # overridden below
) -> IncidentRead:
    """Get incident by UUID."""
    flow = _get_flow(session)
    return await flow.get(incident_id)


@router.put(
    "/{incident_id}",
    response_model=IncidentRead,
    summary="Update an incident",
    description="Update incident fields (title, description, severity, status). Fields not provided are unchanged.",
    operation_id="updateIncident",
)
async def update_incident(
    payload: IncidentUpdate,
    incident_id: uuid.UUID = Path(..., description="Incident UUID."),
    session: Annotated[AsyncSession, Depends(lambda: None)] = None,  # overridden below
) -> IncidentRead:
    """Update incident by UUID."""
    flow = _get_flow(session)
    return await flow.update(incident_id, payload)


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an incident",
    description="Delete an incident by UUID.",
    operation_id="deleteIncident",
)
async def delete_incident(
    incident_id: uuid.UUID = Path(..., description="Incident UUID."),
    session: Annotated[AsyncSession, Depends(lambda: None)] = None,  # overridden below
) -> Response:
    """Delete incident by UUID.

    Returns:
      Response: Empty 204 No Content response.
    """
    flow = _get_flow(session)
    await flow.delete(incident_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# PUBLIC_INTERFACE
def bind_session_dependency(router_to_bind: APIRouter, session_dep):
    """Bind the real DB session dependency to this router.

    This keeps the router functions easy to type-check while allowing app factory to inject
    the dependency (so tests can override it cleanly too).

    Args:
      router_to_bind: The incidents router to bind.
      session_dep: FastAPI dependency callable returning AsyncSession.
    """
    # We used a placeholder `Depends(lambda: None)` in route signatures.
    # Here we override it at runtime by modifying dependency_overrides at app creation time.
    # FastAPI doesn't allow changing Depends objects after definition, so we override the lambda.
    # (This is a stable, centralized pattern used once, rather than scattered ad-hoc dependencies.)
    placeholder = lambda: None  # noqa: E731
    router_to_bind.dependency_overrides_provider.dependency_overrides[placeholder] = session_dep
