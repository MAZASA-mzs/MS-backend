import os
import requests
from datetime import datetime
from app.exceptions import BusinessLogicError
from app.redis_client import redis_client

YANDEX_DISK_BASE_DIR = os.getenv("YANDEX_DISK_BASE_DIR", "observations")
YANDEX_DISK_TOKEN = os.getenv("YANDEX_DISK_TOKEN", "")


def _ensure_yandex_disk_directory(folder_path: str, headers: dict):
    """
    Create directory on Yandex.Disk if it doesn't exist.
    Uses Redis for caching to avoid making requests on every upload.
    """
    cache_key = f"yandex_dir:{folder_path}"

    # skip is folder existence is cached (either exists or was recently created)
    if redis_client.get(cache_key):
        return

    create_dir_url = "https://cloud-api.yandex.net/v1/disk/resources"

    try:
        response = requests.put(
            create_dir_url, headers=headers, params={"path": folder_path}
        )

        # 201 Created — successfully created
        # 409 Conflict — folder already exists
        if response.status_code in (201, 409):
            # Cache the fact that the folder exists for 7 days (604800 seconds)
            redis_client.setex(cache_key, 604800, "1")
        else:
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise BusinessLogicError(
            f"Failed to ensure directory '{folder_path}' exists on Yandex.Disk: {e}"
        )


def upload_file_to_yandex_disk(
    file_bytes: bytes, filename: str, content_type: str
) -> str:
    if not YANDEX_DISK_TOKEN:
        raise BusinessLogicError("Yandex Disk token is missing")

    headers = {"Authorization": f"OAuth {YANDEX_DISK_TOKEN}"}

    # 1. Form the target path on Yandex.Disk based on the current week.
    # %G - ISO year, %V - ISO week number (e.g., 2026-W17)
    week_folder = datetime.now().strftime("%G-W%V")
    base_folder = YANDEX_DISK_BASE_DIR
    target_folder = f"{base_folder}/{week_folder}"
    file_path = f"{target_folder}/{filename}"

    # 2. Ensure that the base folder and the target week folder exist on Yandex.Disk.
    # If not, create them.
    _ensure_yandex_disk_directory(base_folder, headers)
    _ensure_yandex_disk_directory(target_folder, headers)

    # 3. Request an upload URL from Yandex.Disk for the target file path.
    # This URL will be used to upload the file.
    upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
    params = {"path": file_path, "overwrite": "true"}

    try:
        response = requests.get(upload_url, headers=headers, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise BusinessLogicError(
            f"Failed to get Yandex.Disk upload URL for {file_path}: {e}"
        )

    href = response.json().get("href")

    # 4. Upload the file to the provided URL.
    try:
        upload_response = requests.put(
            href, files={"file": (filename, file_bytes, content_type)}
        )
        upload_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise BusinessLogicError(f"Failed to upload file to Yandex.Disk: {e}")

    # Return the Yandex.Disk path to the uploaded file in the format:
    # "disk:/observations/2026-W17/filename.ext".
    return f"disk:/{file_path}"
