from __future__ import annotations

import logging
import uuid
from typing import Sequence, Tuple

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.errors import DatabaseError, NotFoundError
from app.models.incident import Incident
from app.schemas.incidents import IncidentCreate, IncidentUpdate

logger = logging.getLogger(__name__)


class IncidentsService:
    """Service for Incident CRUD.

    This isolates DB concerns from API routing and provides a stable contract for flows.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_incident(self, payload: IncidentCreate) -> Incident:
        try:
            incident = Incident(
                title=payload.title,
                description=payload.description,
                severity=payload.severity,
                status=payload.status,
            )
            self._session.add(incident)
            await self._session.commit()
            await self._session.refresh(incident)
            return incident
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise DatabaseError("Failed to create incident.", details={"reason": str(e)}) from e

    async def list_incidents(self, limit: int, offset: int) -> Tuple[Sequence[Incident], int]:
        try:
            total_stmt = select(func.count()).select_from(Incident)
            items_stmt = (
                select(Incident)
                .order_by(Incident.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            total = (await self._session.execute(total_stmt)).scalar_one()
            items = (await self._session.execute(items_stmt)).scalars().all()
            return items, int(total)
        except SQLAlchemyError as e:
            raise DatabaseError("Failed to list incidents.", details={"reason": str(e)}) from e

    async def get_incident(self, incident_id: uuid.UUID) -> Incident:
        try:
            stmt = select(Incident).where(Incident.id == incident_id)
            incident = (await self._session.execute(stmt)).scalar_one_or_none()
            if incident is None:
                raise NotFoundError("Incident not found.", details={"incident_id": str(incident_id)})
            return incident
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            raise DatabaseError("Failed to fetch incident.", details={"reason": str(e)}) from e

    async def update_incident(self, incident_id: uuid.UUID, payload: IncidentUpdate) -> Incident:
        # Ensure existence first to return clean 404 rather than silent no-op.
        _ = await self.get_incident(incident_id)

        values = payload.model_dump(exclude_unset=True)
        if not values:
            # No changes; just return current state.
            return await self.get_incident(incident_id)

        try:
            stmt = (
                update(Incident)
                .where(Incident.id == incident_id)
                .values(**values)
                .returning(Incident)
            )
            updated = (await self._session.execute(stmt)).scalar_one()
            await self._session.commit()
            return updated
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise DatabaseError("Failed to update incident.", details={"reason": str(e)}) from e

    async def delete_incident(self, incident_id: uuid.UUID) -> None:
        # Ensure clean 404 semantics.
        _ = await self.get_incident(incident_id)

        try:
            stmt = delete(Incident).where(Incident.id == incident_id)
            await self._session.execute(stmt)
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise DatabaseError("Failed to delete incident.", details={"reason": str(e)}) from e
