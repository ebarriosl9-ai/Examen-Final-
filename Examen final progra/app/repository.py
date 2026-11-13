from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ActivoAtendido, Ticket, User


class ActivoRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_ticket(self, ticket_id: int) -> Ticket | None:
        return self.db.get(Ticket, ticket_id)

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def existe_codigo(self, ticket_id: int, codigo: str) -> bool:
        stmt = select(ActivoAtendido.id).where(
            ActivoAtendido.ticket_id == ticket_id, ActivoAtendido.codigo == codigo
        )
        return self.db.execute(stmt).first() is not None

    def agregar(self, activo: ActivoAtendido) -> ActivoAtendido:
        self.db.add(activo)
        self.db.commit()
        self.db.refresh(activo)
        return activo

    def listar_por_ticket(self, ticket_id: int) -> list[ActivoAtendido]:
        stmt = (
            select(ActivoAtendido)
            .where(ActivoAtendido.ticket_id == ticket_id)
            .order_by(ActivoAtendido.id)
        )
        return list(self.db.execute(stmt).scalars())
