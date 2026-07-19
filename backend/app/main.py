from fastapi import FastAPI

# Register all SQLAlchemy models
import app.models

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.cases import router as cases_router
from app.api.investigation import router as investigation_router
from app.api.predictions import router as prediction_router
from app.api.transactions import router as transaction_router
from app.api.users import router as users_router
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(transaction_router)
app.include_router(prediction_router)
app.include_router(admin_router)
app.include_router(investigation_router)
app.include_router(cases_router)


@app.get("/")
def root():
    return {
        "message": "Lynceus Backend Running",
    }