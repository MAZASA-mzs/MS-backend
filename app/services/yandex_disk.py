import os
import requests
from fastapi import UploadFile, HTTPException


def upload_file_to_yandex_disk(file: UploadFile, filename: str) -> str:
    token = os.getenv("YANDEX_DISK_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Yandex Disk token is missing")

    headers = {"Authorization": f"OAuth {token}"}
    upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
    params = {"path": f"observations/{filename}", "overwrite": "true"}

    response = requests.get(upload_url, headers=headers, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to get Yandex.Disk upload URL")

    href = response.json().get("href")

    upload_response = requests.put(href, files={"file": (filename, file.file, file.content_type)})

    if upload_response.status_code != 201:
        raise HTTPException(status_code=500, detail="Failed to upload file to Yandex.Disk")

    return f"disk:/observations/{filename}"
