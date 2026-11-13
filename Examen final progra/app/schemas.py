from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ActivoIn(BaseModel):
    codigo: str = Field(max_length=60)
    descripcion: str = Field(default="", max_length=255)


class ActivoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    codigo: str
    descripcion: str
    registrado_por_id: int
    creado_en: datetime
