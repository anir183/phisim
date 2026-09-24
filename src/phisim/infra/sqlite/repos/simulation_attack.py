from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from phisim.infra.sqlite.models.simulation_attack import SimulationAttack


class SimulationAttackRepository:
    def __init__(self, session: OrmSession) -> None:
        self.session = session

    def create(self, attack: SimulationAttack) -> SimulationAttack:
        self.session.add(attack)
        self.session.commit()
        self.session.refresh(attack)
        return attack

    def get_by_attack_id(self, attack_id: str) -> SimulationAttack | None:
        return self.session.scalar(
            select(SimulationAttack).where(
                SimulationAttack.attack_id == attack_id
            )
        )

    def get_by_victim_token(self, token: str) -> SimulationAttack | None:
        return self.session.scalar(
            select(SimulationAttack)
            .where(SimulationAttack.victim_token == token)
            .order_by(SimulationAttack.updated_at.desc())
        )

    def get_active_by_victim_token(
        self,
        token: str,
    ) -> SimulationAttack | None:
        terminal = {"COMPLETED", "ABANDONED", "EXPIRED", "BLOCKED"}
        return self.session.scalar(
            select(SimulationAttack)
            .where(
                SimulationAttack.victim_token == token,
                SimulationAttack.status.not_in(terminal),
            )
            .order_by(SimulationAttack.updated_at.desc())
        )

    def get_by_run_id(self, run_id: str) -> SimulationAttack | None:
        return self.session.scalar(
            select(SimulationAttack).where(SimulationAttack.run_id == run_id)
        )

    def list_recent(self, limit: int = 5) -> list[SimulationAttack]:
        statement = (
            select(SimulationAttack)
            .order_by(
                SimulationAttack.updated_at.desc(),
                SimulationAttack.attack_id.desc(),
            )
            .limit(limit)
        )
        return list(self.session.scalars(statement))

    def save(self, attack: SimulationAttack) -> SimulationAttack:
        attack.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(attack)
        return attack
