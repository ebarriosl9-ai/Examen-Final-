from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import Base, SessionLocal, engine, get_db
from .models import Ticket, User
from .repository import ActivoRepository
from .schemas import ActivoIn, ActivoOut
from .service import ActivoService, DomainError

STATIC_DIR = Path(__file__).parent / "static"


def seed():
    with SessionLocal() as db:
        if db.execute(select(User.id)).first():
            return
        db.add_all(
            [
                User(id=1, username="ana_solicitante", role="solicitante"),
                User(id=2, username="tomas_tecnico", role="tecnico"),
                User(id=3, username="sara_supervisor", role="supervisor"),
                User(id=4, username="admin", role="administrador"),
            ]
        )
        db.add_all(
            [
                Ticket(id=1, titulo="Laptop no enciende", solicitante_id=1),
                Ticket(id=2, titulo="Impresora sin tinta", solicitante_id=1),
            ]
        )
        db.commit()


def create_app() -> FastAPI:
    Base.metadata.create_all(engine)
    seed()

    app = FastAPI(title="HelpDesk EDU - Ficha 03 Activos atendidos")

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    def get_service(db: Session = Depends(get_db)) -> ActivoService:
        return ActivoService(ActivoRepository(db))

    @app.post("/api/tickets/{ticket_id}/assets", response_model=ActivoOut, status_code=201)
    def registrar_activo(
        ticket_id: int,
        body: ActivoIn,
        actor: User = Depends(get_current_user),
        service: ActivoService = Depends(get_service),
    ):
        return service.registrar(actor, ticket_id, body.codigo, body.descripcion)

    @app.get("/api/tickets/{ticket_id}/assets", response_model=list[ActivoOut])
    def listar_activos(
        ticket_id: int,
        actor: User = Depends(get_current_user),
        service: ActivoService = Depends(get_service),
    ):
        return service.listar(actor, ticket_id)

    @app.get("/api/tickets")
    def listar_tickets(actor: User = Depends(get_current_user), db: Session = Depends(get_db)):
        tickets = db.execute(select(Ticket).order_by(Ticket.id)).scalars()
        return [{"id": t.id, "titulo": t.titulo, "estado": t.estado} for t in tickets]

    @app.get("/api/users")
    def listar_usuarios(db: Session = Depends(get_db)):
        users = db.execute(select(User).order_by(User.id)).scalars()
        return [{"id": u.id, "username": u.username, "role": u.role} for u in users]

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index():
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
