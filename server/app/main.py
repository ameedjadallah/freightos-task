from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.app.routes import upload, compare

app = FastAPI()


# Allow CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow React frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(upload.router)
app.include_router(compare.router)


@app.on_event("startup")
async def startup_event():
    """Runs when the FastAPI app starts."""
    print("🚀 Running aggregation process on startup...")
    # Uncomment this to import market rates
    # base_dir = os.path.dirname(os.path.abspath(__file__))  # Get directory of main.py
    # file_path = os.path.join(base_dir, "Market Row Data.xlsx")
    # import_market_rates(file_path)  # Import market rates first


@app.get("/")
def home():
    """Root endpoint for API health check."""
    return "Welcome to the Freightos Shipping price tool 🚢"
