from fastapi import FastAPI
from app.routers.users import router as users_router
from app.middleware.api_key import APIKeyMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Main Backend API", version="1.0.0")

app.add_middleware(APIKeyMiddleware, api_key=os.getenv("API_KEY"))

app.include_router(users_router, prefix="/api/users", tags=["users"])


@app.get("/")
def read_root():
    return {"message": "Main Backend API"}
