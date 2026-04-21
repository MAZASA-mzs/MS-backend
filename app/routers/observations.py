import uuid
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.ai_service import classify_and_stash_image, get_plants_dictionary
from app.services.observation_service import (
    create_geolocation,
    link_photo_geo,
    get_user_stats,
    process_and_create_post,
)
from app.schemas.observation import (
    AIClassificationResponse,
    PostCreate,
    PostCreateResponse,
    GeolocationCreate,
    GeolocationResponse,
    LinkPhotoGeo,
)

router = APIRouter()


@router.get("/plants/dictionary")
async def get_supported_plants():
    """Эндпоинт для ботов: получить актуальный список растений"""
    return await get_plants_dictionary()


@router.post("/ai/classify", response_model=AIClassificationResponse)
async def proxy_ai_classification(file: UploadFile = File(...)):
    """Send file to AI service, get classification result and temp_file_id"""
    return await classify_and_stash_image(file)


@router.post("/posts", response_model=PostCreateResponse)
def upload_post(payload: PostCreate, db: Session = Depends(get_db)):
    """Create new post with given data, link it to user and return post_id and link"""
    post = process_and_create_post(db, payload)

    return {
        "post_id": post.post_id,
        "link": post.link,
    }


@router.post("/geolocations", response_model=GeolocationResponse)
def save_geolocation(geo: GeolocationCreate, db: Session = Depends(get_db)):
    geo_obj = create_geolocation(db, str(geo.user_id), geo.x, geo.y)
    return {"geo_id": geo_obj.geo_id}


@router.post("/link-photo-geo")
def link_photo_geo_endpoint(payload: LinkPhotoGeo, db: Session = Depends(get_db)):
    link_photo_geo(db, str(payload.user_id), str(payload.post_id), str(payload.geo_id))
    return {"message": "Linked successfully"}


@router.get("/user-stats")
def user_stats(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user_stats_result = get_user_stats(db, str(user_id))
    return {
        "post_count": user_stats_result.post_count,
        "geo_count": user_stats_result.geo_count,
    }
