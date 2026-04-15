from pydantic import BaseModel

class ProfileData(BaseModel):
    id: str
    name: str
    gender: str
    gender_probability: float
    sample_size: int
    age: int
    age_group: str
    country_id: str
    country_probability: float
    created_at: str

  


class ProfileResponse(BaseModel):
    status: str
    data: ProfileData
   