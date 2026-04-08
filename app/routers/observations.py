import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.yandex_disk import upload_file_to_yandex_disk
from app.services.observation_service import create_post, create_geolocation, link_photo_geo
from app.schemas.observation import PostCreateResponse, GeolocationCreate, GeolocationResponse, LinkPhotoGeo

router = APIRouter()


@router.post("/posts", response_model=PostCreateResponse)
def upload_post(
        user_id: uuid.UUID = Form(...),
        description: str = Form(""),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    # Upload to Yandex Drive
    filename = f"{uuid.uuid4()}_{file.filename}"
    link = upload_file_to_yandex_disk(file, filename)

    # Save to DB
    post = create_post(db, str(user_id), link, description)
    return {"post_id": post.post_id, "link": post.link}


@router.post("/geolocations", response_model=GeolocationResponse)
def save_geolocation(geo: GeolocationCreate, db: Session = Depends(get_db)):
    geo_obj = create_geolocation(db, str(geo.user_id), geo.x, geo.y)
    return {"geo_id": geo_obj.geo_id}


@router.post("/link_photo_geo")
def link_photo_geo_endpoint(payload: LinkPhotoGeo, db: Session = Depends(get_db)):
    link_photo_geo(db, str(payload.user_id), str(payload.post_id), str(payload.geo_id))
    return {"message": "Linked successfully"}
