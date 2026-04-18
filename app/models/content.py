import uuid
from sqlalchemy import Column, String, Text, Float, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

post_users = Table(
    "post_users",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.user_id")),
    Column("post_id", UUID(as_uuid=True), ForeignKey("posts.post_id")),
)

post_geolocations = Table(
    "post_geolocations",
    Base.metadata,
    Column("post_id", UUID(as_uuid=True), ForeignKey("posts.post_id")),
    Column("geo_id", UUID(as_uuid=True), ForeignKey("geolocations.geo_id")),
)

user_geolocations = Table(
    "user_geolocations",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.user_id")),
    Column("geo_id", UUID(as_uuid=True), ForeignKey("geolocations.geo_id")),
)


class Post(Base):
    __tablename__ = "posts"

    post_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    link = Column(String, nullable=False)
    post_description = Column(Text, nullable=True)


class Geolocation(Base):
    __tablename__ = "geolocations"

    geo_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
