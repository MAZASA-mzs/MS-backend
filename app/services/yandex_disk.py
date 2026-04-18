import os
import requests
from fastapi import UploadFile
from app.exceptions import BusinessLogicError


def upload_file_to_yandex_disk(file: UploadFile, filename: str) -> str:
    token = os.getenv("YANDEX_DISK_TOKEN")
    if not token:
        raise BusinessLogicError("Yandex Disk token is missing")

    headers = {"Authorization": f"OAuth {token}"}
    upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
    params = {"path": f"observations/{filename}", "overwrite": "true"}

    try:
        response = requests.get(upload_url, headers=headers, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        raise BusinessLogicError(f"Failed to get Yandex.Disk upload URL: {e}")

    href = response.json().get("href")

    try:
        upload_response = requests.put(
            href, files={"file": (filename, file.file, file.content_type)}
        )
        upload_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise BusinessLogicError(f"Failed to upload file to Yandex.Disk: {e}")

    return f"disk:/observations/{filename}"
