from pydantic import BaseModel

class ProfileData(BaseModel):

    name: str
  


class ProfileResponse(BaseModel):
    status: str
    data: ProfileData
   