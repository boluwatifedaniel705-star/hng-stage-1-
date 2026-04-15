from pydantic import BaseModel

class ProfileResponse(BaseModel):
    status: str
    data: dict

    from pydantic import BaseModel

class ProfileRequest(BaseModel):
    name: str