import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import analysis, auth


def create_app() -> FastAPI:
    app = FastAPI(title="Video Clip Selection Platform", version="1.0.0")

    # Default CORS origins - allow localhost for frontend (all common ports)
    allowed_origins = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:5173,http://localhost:5174,http://localhost:3000,http://localhost:5175,http://127.0.0.1:5173,http://127.0.0.1:5174"
    )
    origins = [o.strip() for o in allowed_origins.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(analysis.router, prefix="/api")
    app.include_router(auth.router, prefix="/api/auth")
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)


