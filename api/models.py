from pydantic import BaseModel


class ProfileIn(BaseModel):
    name: str


class ProfileOut(BaseModel):
    id: int
    name: str
    created_at: str


class DacPathIn(BaseModel):
    name: str
    notes: str | None = None


class DacPathPatch(BaseModel):
    name: str | None = None
    notes: str | None = None


class DacPathOut(BaseModel):
    id: int
    name: str
    notes: str | None
    created_at: str
