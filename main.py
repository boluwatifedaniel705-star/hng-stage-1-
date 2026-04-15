from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from schemas import ProfileRequest, ProfileResponse
import httpx
from database import Base, engine, SessionLocal
from models import Profile
from utils import generate_uuid_v7, utc_now, classify_age_group

Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS for HNG grading
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/profiles", response_model=ProfileResponse)
async def create_profile(payload: ProfileRequest, db: Session = Depends(get_db)):
    # Validation
    if "name" not in payload or not payload["name"]:
        raise HTTPException(
            status_code=400,
            detail={"status": "error", "message": "Name is required"}
        )

    name = payload.name

    if not isinstance(name, str):
        raise HTTPException(
            status_code=422,
            detail={"status": "error", "message": "Name must be a string"}
        )

    # Idempotency
    existing = db.query(Profile).filter(Profile.name == name).first()
    if existing:
        return {
    "status": "success",
    "data": {
        "id": new_profile.id,
        "name": new_profile.name,
        "gender": new_profile.gender,
        "gender_probability": new_profile.gender_probability,
        "sample_size": new_profile.sample_size,
        "age": new_profile.age,
        "age_group": new_profile.age_group,
        "country_id": new_profile.country_id,
        "country_probability": new_profile.country_probability,
        "created_at": new_profile.created_at,
    }
}

    # Call external APIs
    async with httpx.AsyncClient() as client:
        g = await client.get(f"https://api.genderize.io?name={name}")
        a = await client.get(f"https://api.agify.io?name={name}")
        n = await client.get(f"https://api.nationalize.io?name={name}")

    gender_data = g.json()
    age_data = a.json()
    nat_data = n.json()

    # Edge cases
    if gender_data.get("gender") is None or gender_data.get("count", 0) == 0:
        raise HTTPException(
            status_code=404,
            detail={"status": "error", "message": "Gender data unavailable"}
        )

    if age_data.get("age") is None:
        raise HTTPException(
            status_code=404,
            detail={"status": "error", "message": "Age data unavailable"}
        )

    if not nat_data.get("country"):
        raise HTTPException(
            status_code=404,
            detail={"status": "error", "message": "Country data unavailable"}
        )

    # Country with highest probability
    best_country = max(nat_data["country"], key=lambda c: c["probability"])

    # Process data
    new_profile = Profile(
        id=generate_uuid_v7(),
        name=name,
        gender=gender_data["gender"],
        gender_probability=gender_data["probability"],
        sample_size=gender_data["count"],
        age=age_data["age"],
        age_group=classify_age_group(age_data["age"]),
        country_id=best_country["country_id"],
        country_probability=best_country["probability"],
        created_at=utc_now(),
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    # Success response
    return {
    "status": "success",
    "data": {
        "id": new_profile.id,
        "name": new_profile.name,
        "gender": new_profile.gender,
        "gender_probability": new_profile.gender_probability,
        "sample_size": new_profile.sample_size,
        "age": new_profile.age,
        "age_group": new_profile.age_group,
        "country_id": new_profile.country_id,
        "country_probability": new_profile.country_probability,
        "created_at": new_profile.created_at,
    }
}