from pydantic import BaseModel
from uuid import UUID

class PostCreateResponse(BaseModel):
    post_id: UUID
    link: str

class GeolocationCreate(BaseModel):
    user_id: UUID
    x: float
    y: float

class GeolocationResponse(BaseModel):
    geo_id: UUID

class LinkPhotoGeo(BaseModel):
    user_id: UUID
    post_id: UUID
    geo_id: UUID
