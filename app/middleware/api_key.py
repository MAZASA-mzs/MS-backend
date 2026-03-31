from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class APIKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_key: str):
        super().__init__(app)
        self.api_key = api_key

    async def dispatch(self, request: Request, call_next):
        if request.headers.get("X-Api-Key") != self.api_key:
            raise HTTPException(status_code=403, detail="Invalid API Key")
        response = await call_next(request)
        return response
