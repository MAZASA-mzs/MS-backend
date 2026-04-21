import os
import json
import uuid
import httpx
import base64
from fastapi import UploadFile
from app.redis_client import redis_client
from app.exceptions import BusinessLogicError

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8000")
PLANTS_CACHE_KEY = "ai:plants_dict"


async def get_plants_dictionary() -> dict:
    """Get the plants dictionary from Redis cache or sync with AI if not available."""
    cached = redis_client.get(PLANTS_CACHE_KEY)
    if cached:
        return json.loads(cached)

    return await sync_plants_dictionary()


async def sync_plants_dictionary() -> dict:
    """Get the latest plants list from AI and save it to Redis."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{AI_SERVICE_URL}/plants")
            response.raise_for_status()
            plants_data = response.json()

            # Save to Redis with an expiration time (e.g., 24 hours)
            redis_client.setex(PLANTS_CACHE_KEY, 86400, json.dumps(plants_data))
            return plants_data
        except Exception as e:
            raise BusinessLogicError(f"Failed to sync plants from AI: {e}")


async def classify_and_stash_image(file: UploadFile) -> dict:
    """Send file to AI service and stash it in Redis."""
    file_bytes = await file.read()

    # 1. Send file to AI service for classification
    async with httpx.AsyncClient() as client:
        try:
            files = {"file": (file.filename, file_bytes, file.content_type)}
            response = await client.post(f"{AI_SERVICE_URL}/classify", files=files)
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            raise BusinessLogicError(f"AI classification failed: {e}")

    # 2. Save file in Redis (Base64) for 1 hour (3600 sec)
    temp_file_id = str(uuid.uuid4())
    b64_data = base64.b64encode(file_bytes).decode("utf-8")

    stash_payload = {
        "filename": file.filename,
        "content_type": file.content_type,
        "data": b64_data,
    }
    redis_client.setex(f"temp_file:{temp_file_id}", 3600, json.dumps(stash_payload))

    # 3. Add reference image URL to the result if classification was successful
    if result.get("plant_class") != -1:
        class_str = str(result["plant_class"])
        plants_dict = await get_plants_dictionary()
        if class_str in plants_dict:
            result["reference_image_url"] = plants_dict[class_str].get(
                "reference_image_url", ""
            )

    # IMPORTANT: Return temp_file_id to the client for later retrieval
    result["temp_file_id"] = temp_file_id
    return result


def get_and_delete_stashed_image(temp_file_id: str) -> dict:
    """Get file from Redis by ID and delete it."""
    key = f"temp_file:{temp_file_id}"
    stashed_data_str = redis_client.get(key)

    if not stashed_data_str:
        return None

    stashed_data = json.loads(stashed_data_str)
    stashed_data["bytes"] = base64.b64decode(stashed_data["data"])

    redis_client.delete(key)
    return stashed_data
