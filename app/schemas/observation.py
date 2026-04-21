from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class AIClassificationResponse(BaseModel):
    plant_class: int
    confidence: float
    name: Optional[str] = None
    description: Optional[str] = None
    danger: Optional[str] = None
    color: Optional[str] = None
    reference_image_url: Optional[str] = None
    message: Optional[str] = None
    temp_file_id: Optional[str] = None


class PostCreate(BaseModel):
    user_id: UUID
    description: Optional[str] = ""
    ai_plant_id: int
    ai_confidence: float = 0.0
    user_plant_id: int
    temp_file_id: str


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
