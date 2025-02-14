from fastapi import FastAPI
from server.app.routes import router

app = FastAPI()

# Register routes
app.include_router(router)


@app.get("/")
def home():
    """Root endpoint for API health check."""
    return {"message": "Welcome to the Freightos API"}
