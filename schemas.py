from pydantic import BaseModel

class ProfileResponse(BaseModel):
    status: str
    data: dict