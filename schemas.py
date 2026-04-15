from pydantic import BaseModel

# INPUT MODEL (request body)
class ProfileRequest(BaseModel):
    name: str


# OUTPUT MODEL (data returned inside "data")
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


# FULL RESPONSE MODEL
class ProfileResponse(BaseModel):
    status: str
    data: ProfileData
   