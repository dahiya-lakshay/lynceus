from fastapi import FastAPI

from app.config import settings

# Import every model once so SQLAlchemy registers them
import app.models.user
import app.models.transaction
import app.models.prediction

from app.api.auth import router as auth_router


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "message": "Lynceus Backend Running",
    }