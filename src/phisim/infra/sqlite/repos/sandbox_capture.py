from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.models.sandbox_capture import SandboxCapture


class SandboxCaptureRepository:
    def __init__(self, session: OrmSession) -> None:
        self.session = session

    def create(self, capture: SandboxCapture) -> SandboxCapture:
        self.session.add(capture)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
        self.session.refresh(capture)
        return capture

    def get_by_capture_id(self, capture_id: str) -> SandboxCapture | None:
        return self.session.scalar(
            select(SandboxCapture).where(
                SandboxCapture.capture_id == capture_id
            )
        )

    def list_by_session(self, session_id: str) -> list[SandboxCapture]:
        statement = (
            select(SandboxCapture)
            .where(SandboxCapture.session_id == session_id)
            .order_by(SandboxCapture.created_at, SandboxCapture.id)
        )
        return list(self.session.scalars(statement))
