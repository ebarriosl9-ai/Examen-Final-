from .models import ActivoAtendido, User
from .repository import ActivoRepository

ROLES_PERSONAL = {"tecnico", "supervisor", "administrador"}


class DomainError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFound(DomainError):
    status_code = 404


class Forbidden(DomainError):
    status_code = 403


class Conflict(DomainError):
    status_code = 409


class ActivoService:
    def __init__(self, repo: ActivoRepository):
        self.repo = repo

    def _verificar_personal(self, actor: User):
        if actor.role not in ROLES_PERSONAL:
            raise Forbidden("Solo el personal puede gestionar activos atendidos.")

    def _ticket_o_404(self, ticket_id: int):
        ticket = self.repo.get_ticket(ticket_id)
        if ticket is None:
            raise NotFound("El ticket no existe.")
        return ticket

    def registrar(self, actor: User, ticket_id: int, codigo: str, descripcion: str) -> ActivoAtendido:
        self._verificar_personal(actor)
        self._ticket_o_404(ticket_id)

        codigo = (codigo or "").strip().upper()
        if not codigo:
            raise DomainError("El código de activo no puede estar vacío.")
        if self.repo.existe_codigo(ticket_id, codigo):
            raise Conflict(f"El activo '{codigo}' ya fue registrado en este ticket.")

        activo = ActivoAtendido(
            ticket_id=ticket_id,
            codigo=codigo,
            descripcion=(descripcion or "").strip(),
            registrado_por_id=actor.id,
        )
        return self.repo.agregar(activo)

    def listar(self, actor: User, ticket_id: int) -> list[ActivoAtendido]:
        self._verificar_personal(actor)
        self._ticket_o_404(ticket_id)
        return self.repo.listar_por_ticket(ticket_id)
