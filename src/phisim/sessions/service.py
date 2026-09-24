from datetime import UTC, datetime
from uuid import uuid4

from phisim.infra.sqlite.models.session import Session as SessionModel
from phisim.infra.sqlite.repos.scenario import ScenarioRepository
from phisim.infra.sqlite.repos.session import SessionRepository
from phisim.sessions.schemas import SessionCreate, SessionStatus


class DuplicateSessionError(Exception):
    pass


class SessionScenarioNotFoundError(Exception):
    pass


class SessionNotFoundError(Exception):
    pass


class SessionService:
    def __init__(
        self,
        repository: SessionRepository,
        scenario_repository: ScenarioRepository,
    ) -> None:
        self.repository = repository
        self.scenario_repository = scenario_repository

    def create(self, session_data: SessionCreate) -> SessionModel:
        scenario = self.scenario_repository.get_by_scenario_id(
            session_data.scenario_id
        )

        if scenario is None:
            raise SessionScenarioNotFoundError

        session_id = session_data.session_id or str(uuid4())

        if self.repository.get_by_session_id(session_id) is not None:
            raise DuplicateSessionError

        session = SessionModel(
            session_id=session_id,
            scenario_id=session_data.scenario_id,
            started_at=datetime.now(UTC),
            completed_at=None,
            status=SessionStatus.ACTIVE.value,
        )

        return self.repository.create(session)

    def get(self, session_id: str) -> SessionModel:
        session = self.repository.get_by_session_id(session_id)

        if session is None:
            raise SessionNotFoundError

        return session

    def list_all(self) -> list[SessionModel]:
        return self.repository.list_all()

    def complete(self, session_id: str) -> SessionModel:
        session = self.get(session_id)

        if session.status == SessionStatus.COMPLETED.value:
            return session

        session.status = SessionStatus.COMPLETED.value
        session.completed_at = datetime.now(UTC)

        return self.repository.save(session)
