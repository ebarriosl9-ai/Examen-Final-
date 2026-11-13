import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import ActivoAtendido, Ticket, User


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session() as db:
        db.add_all(
            [
                User(id=1, username="ana", role="solicitante"),
                User(id=2, username="tomas", role="tecnico"),
            ]
        )
        db.add_all([Ticket(id=1, titulo="T1", solicitante_id=1), Ticket(id=2, titulo="T2", solicitante_id=1)])
        db.commit()
    return Session


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


TEC = {"Authorization": "Bearer token-2"}
SOL = {"Authorization": "Bearer token-1"}


def test_camino_feliz_persiste_en_otra_sesion(client, session_factory):
    r = client.post(
        "/api/tickets/1/assets",
        json={"codigo": "lap-001", "descripcion": "Laptop Dell"},
        headers=TEC,
    )
    assert r.status_code == 201
    assert r.json()["codigo"] == "LAP-001"

    with session_factory() as db:
        activos = db.execute(select(ActivoAtendido).where(ActivoAtendido.ticket_id == 1)).scalars().all()
        assert [a.codigo for a in activos] == ["LAP-001"]

    lista = client.get("/api/tickets/1/assets", headers=TEC).json()
    assert len(lista) == 1 and lista[0]["descripcion"] == "Laptop Dell"


def test_codigo_duplicado_en_mismo_ticket_se_rechaza_sin_asociar_otro(client, session_factory):
    client.post("/api/tickets/1/assets", json={"codigo": "PC-9", "descripcion": "a"}, headers=TEC)
    r = client.post("/api/tickets/1/assets", json={"codigo": " pc-9 ", "descripcion": "b"}, headers=TEC)
    assert r.status_code == 409

    with session_factory() as db:
        total = db.execute(select(ActivoAtendido).where(ActivoAtendido.ticket_id == 1)).scalars().all()
        assert len(total) == 1
        assert total[0].descripcion == "a"


def test_mismo_codigo_en_otro_ticket_si_se_permite(client):
    assert client.post("/api/tickets/1/assets", json={"codigo": "X1"}, headers=TEC).status_code == 201
    assert client.post("/api/tickets/2/assets", json={"codigo": "X1"}, headers=TEC).status_code == 201


def test_codigo_vacio_se_rechaza(client, session_factory):
    r = client.post("/api/tickets/1/assets", json={"codigo": "   "}, headers=TEC)
    assert r.status_code == 400
    with session_factory() as db:
        assert db.execute(select(ActivoAtendido)).first() is None


def test_solicitante_no_puede_registrar_ni_ver(client, session_factory):
    assert client.post("/api/tickets/1/assets", json={"codigo": "A1"}, headers=SOL).status_code == 403
    assert client.get("/api/tickets/1/assets", headers=SOL).status_code == 403
    with session_factory() as db:
        assert db.execute(select(ActivoAtendido)).first() is None


def test_sin_token_401_y_ticket_inexistente_404(client):
    assert client.post("/api/tickets/1/assets", json={"codigo": "A1"}).status_code == 401
    assert client.post("/api/tickets/99/assets", json={"codigo": "A1"}, headers=TEC).status_code == 404
