from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from routes.recommendation_routes import router as recommendation_router
from routes.health_routes import router as health_router
from controllers.recommendation_controller import load_ml_resources

load_dotenv()

app = FastAPI()

origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """
    Import heavy modules and load data after FastAPI starts,
    so Render detects the open port quickly.
    """
    load_ml_resources()

app.include_router(recommendation_router)
app.include_router(health_router)