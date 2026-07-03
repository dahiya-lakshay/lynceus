from fastapi import FastAPI

# Importing all models so that SQLAlchemy can register them
import app.models

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.transactions import router as transaction_router
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(transaction_router)


@app.get("/")
def root():
    return {
        "message": "Lynceus Backend Running",
    }