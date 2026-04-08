from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from app.routers.users import router as users_router
from app.routers.observations import router as observations_router
from app.routers.settings import router as settings_router
from app.routers.admin import router as admin_router
from app.middleware.api_key import verify_api_key
from app.exceptions import NotFoundError, InvalidReferenceError, BusinessLogicError


load_dotenv()

app = FastAPI(
    title="Main Backend API",
    version="1.0.0",
    dependencies=[Depends(verify_api_key)]
)

@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": exc.message},
    )

@app.exception_handler(InvalidReferenceError)
async def invalid_reference_exception_handler(request: Request, exc: InvalidReferenceError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.message},
    )

@app.exception_handler(BusinessLogicError)
async def business_logic_exception_handler(request: Request, exc: BusinessLogicError):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message},
    )

app.include_router(users_router, prefix="/api/users", tags=["users"])
app.include_router(observations_router, prefix="/api", tags=["observations"])

app.include_router(settings_router, prefix="/api", tags=["settings", "public"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])

@app.get("/")
def read_root():
    return {"message": "Main Backend API is up and running!"}
