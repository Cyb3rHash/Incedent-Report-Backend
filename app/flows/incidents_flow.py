from __future__ import annotations

import logging
import uuid

from app.schemas.incidents import IncidentCreate, IncidentListResponse, IncidentRead, IncidentUpdate
from app.services.incidents_service import IncidentsService

logger = logging.getLogger(__name__)


class IncidentsFlow:
    """IncidentsFlow - canonical orchestration for incident CRUD use-cases.

    Contracts:
      Inputs:
        - Validated Pydantic payloads (IncidentCreate/IncidentUpdate)
        - Pagination parameters with constraints enforced at API boundary
      Outputs:
        - ORM-backed incident results converted by Pydantic response models at API boundary
      Errors:
        - Raises AppError subclasses (e.g., NotFoundError, DatabaseError)
      Side effects:
        - Writes to the database via service layer
      Observability:
        - Logs start/end per operation with incident_id where applicable
    """

    def __init__(self, service: IncidentsService):
        self._service = service

    async def create(self, payload: IncidentCreate) -> IncidentRead:
        logger.info("IncidentsFlow.create start title=%s", payload.title)
        incident = await self._service.create_incident(payload)
        logger.info("IncidentsFlow.create success incident_id=%s", incident.id)
        return IncidentRead.model_validate(incident)

    async def list(self, limit: int, offset: int) -> IncidentListResponse:
        logger.info("IncidentsFlow.list start limit=%s offset=%s", limit, offset)
        items, total = await self._service.list_incidents(limit=limit, offset=offset)
        logger.info("IncidentsFlow.list success count=%s total=%s", len(items), total)
        return IncidentListResponse(
            items=[IncidentRead.model_validate(i) for i in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get(self, incident_id: uuid.UUID) -> IncidentRead:
        logger.info("IncidentsFlow.get start incident_id=%s", incident_id)
        incident = await self._service.get_incident(incident_id)
        logger.info("IncidentsFlow.get success incident_id=%s", incident_id)
        return IncidentRead.model_validate(incident)

    async def update(self, incident_id: uuid.UUID, payload: IncidentUpdate) -> IncidentRead:
        logger.info("IncidentsFlow.update start incident_id=%s", incident_id)
        incident = await self._service.update_incident(incident_id, payload)
        logger.info("IncidentsFlow.update success incident_id=%s", incident_id)
        return IncidentRead.model_validate(incident)

    async def delete(self, incident_id: uuid.UUID) -> None:
        logger.info("IncidentsFlow.delete start incident_id=%s", incident_id)
        await self._service.delete_incident(incident_id)
        logger.info("IncidentsFlow.delete success incident_id=%s", incident_id)
