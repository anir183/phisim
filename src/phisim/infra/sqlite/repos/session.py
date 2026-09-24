from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.models.session import Session as SessionModel


class SessionRepository:
    def __init__(self, session: OrmSession) -> None:
        self.session = session

    def create(self, session: SessionModel) -> SessionModel:
        self.session.add(session)

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise

        self.session.refresh(session)

        return session

    def get_by_session_id(self, session_id: str) -> SessionModel | None:
        statement = select(SessionModel).where(
            SessionModel.session_id == session_id
        )

        return self.session.scalar(statement)

    def list_all(self) -> list[SessionModel]:
        statement = select(SessionModel).order_by(
            SessionModel.started_at,
            SessionModel.session_id,
        )

        return list(self.session.scalars(statement))

    def save(self, session: SessionModel) -> SessionModel:
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise

        self.session.refresh(session)

        return session
