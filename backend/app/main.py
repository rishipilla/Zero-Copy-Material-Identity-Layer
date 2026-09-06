from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.materials import router as materials_router


app = FastAPI(
    title="Zero-Copy Material Identity API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(materials_router)


@app.get("/")
def root():
    return {
        "message": "Zero-Copy Material Identity API is running."
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }