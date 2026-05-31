from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routers import auth, plans, users
from .core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.OPENAI_API_KEY.strip():
        raise ValueError(
            "OPENAI_API_KEY is not configured. "
            "Set it in the .env file or as an environment variable."
        )
    yield


app = FastAPI(title="AI Study Planner", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(plans.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
