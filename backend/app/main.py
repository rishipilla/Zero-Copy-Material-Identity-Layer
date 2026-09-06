from fastapi import FastAPI

from app.api.materials import router as materials_router


app = FastAPI(
    title="Zero-Copy Material Identity API",
    version="0.1.0",
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