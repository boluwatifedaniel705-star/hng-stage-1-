from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import httpx
from sqlalchemy import and_
from schemas import ProfileRequest, ProfileResponse
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

    #  Correct validation
    if not payload.name:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Name is required"}
        )

    name = payload.name

    #  Idempotency check
    existing = db.query(Profile).filter(Profile.name == name).first()
    if existing:
        return {
            "status": "success",
            "message": "Profile already exists",
            "data": {
                "id": existing.id,
                "name": existing.name,
                "gender": existing.gender,
                "gender_probability": existing.gender_probability,
                "sample_size": existing.sample_size,
                "age": existing.age,
                "age_group": existing.age_group,
                "country_id": existing.country_id,
                "country_probability": existing.country_probability,
                "created_at": existing.created_at,
            }
        }

    #  Call external APIs
    async with httpx.AsyncClient() as client:
        g = await client.get(f"https://api.genderize.io?name={name}")
        a = await client.get(f"https://api.agify.io?name={name}")
        n = await client.get(f"https://api.nationalize.io?name={name}")

    gender_data = g.json()
    age_data = a.json()
    nat_data = n.json()

    #  Edge cases
    if gender_data.get("gender") is None or gender_data.get("count", 0) == 0:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "Gender data unavailable"}
        )

    if age_data.get("age") is None:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "Age data unavailable"}
        )

    if not nat_data.get("country"):
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "Country data unavailable"}
        )

    #  Get highest probability country
    best_country = max(nat_data["country"], key=lambda c: c["probability"])

    # Save to DB
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

@app.get("/api/profiles/{profile_id}")
async def get_profile(profile_id: str, db: Session = Depends(get_db)):

    profile = db.query(Profile).filter(Profile.id == profile_id).first()

    if not profile:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "Profile not found"}
        )

    return {
        "status": "success",
        "data": {
            "id": profile.id,
            "name": profile.name,
            "gender": profile.gender,
            "gender_probability": profile.gender_probability,
            "sample_size": profile.sample_size,
            "age": profile.age,
            "age_group": profile.age_group,
            "country_id": profile.country_id,
            "country_probability": profile.country_probability,
            "created_at": profile.created_at,
        }
    }

@app.get("/api/profiles")
async def get_profiles(
    gender: str = None,
    country_id: str = None,
    age_group: str = None,
    db: Session = Depends(get_db)
):

    query = db.query(Profile)

    if gender:
        query = query.filter(Profile.gender.ilike(gender))
    if country_id:
        query = query.filter(Profile.country_id.ilike(country_id))
    if age_group:
        query = query.filter(Profile.age_group.ilike(age_group))

    profiles = query.all()

    return {
        "status": "success",
        "count": len(profiles),
        "data": [
            {
                "id": p.id,
                "name": p.name,
                "gender": p.gender,
                "age": p.age,
                "age_group": p.age_group,
                "country_id": p.country_id,
            }
            for p in profiles
        ]
    }

@app.delete("/api/profiles/{profile_id}")
async def delete_profile(profile_id: str, db: Session = Depends(get_db)):

    profile = db.query(Profile).filter(Profile.id == profile_id).first()

    if not profile:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "Profile not found"}
        )

    db.delete(profile)
    db.commit()

    return JSONResponse(status_code=204, content=None)