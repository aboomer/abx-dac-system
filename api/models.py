from pydantic import BaseModel


class ProfileIn(BaseModel):
    name: str


class ProfileOut(BaseModel):
    id: int
    name: str
    created_at: str
