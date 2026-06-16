from fastapi import FastAPI

app = FastAPI(
    title="Lynceus",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "Lynceus Backend Running"}