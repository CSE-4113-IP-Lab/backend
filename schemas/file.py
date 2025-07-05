from pydantic import BaseModel

class FileBase(BaseModel):
    id: int
    url: str

    class Config:
        from_attributes = True