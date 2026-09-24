from sqlalchemy import select
from sqlalchemy.orm import Session

from phisim.infra.sqlite.models.event import Event


class EventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, event: Event) -> Event:
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)

        return event

    def get_by_event_id(self, event_id: str) -> Event | None:
        statement = select(Event).where(Event.event_id == event_id)

        return self.session.scalar(statement)

    def list_by_session(
        self,
        session_id: str,
    ) -> list[Event]:
        statement = select(Event).where(Event.session_id == session_id).order_by(Event.timestamp)

        return list(self.session.scalars(statement))
