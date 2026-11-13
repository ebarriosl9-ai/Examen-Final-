from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    role: Mapped[str] = mapped_column(String(20))


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200))
    estado: Mapped[str] = mapped_column(String(20), default="abierto")
    solicitante_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    activos: Mapped[list["ActivoAtendido"]] = relationship(
        back_populates="ticket", order_by="ActivoAtendido.id"
    )


class ActivoAtendido(Base):

    __tablename__ = "activos_atendidos"
    __table_args__ = (
        UniqueConstraint("ticket_id", "codigo", name="uq_activo_ticket_codigo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(60))
    descripcion: Mapped[str] = mapped_column(String(255), default="")
    registrado_por_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    ticket: Mapped["Ticket"] = relationship(back_populates="activos")
