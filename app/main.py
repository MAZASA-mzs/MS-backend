from fastapi import FastAPI, Depends
from dotenv import load_dotenv
from app.routers.users import router as users_router
from app.middleware.api_key import verify_api_key

load_dotenv()

app = FastAPI(
    title="Main Backend API", 
    version="1.0.0",
    dependencies=[Depends(verify_api_key)] 
)

app.include_router(users_router, prefix="/api/users", tags=["users"])


@app.get("/")
def read_root():
    return {"message": "Main Backend API"}
