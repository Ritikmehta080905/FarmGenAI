from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.buyer_routes import router as buyer_router
from .routes.farmer_routes import router as farmer_router
from .routes.negotiation_routes import router as negotiation_router
from .routes.simulation_routes import router as simulation_router
from .routes.warehouse_routes import router as warehouse_router

app = FastAPI(title="AgriNegotiator API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(buyer_router, prefix="/api/buyer", tags=["Buyer"])
app.include_router(farmer_router, prefix="/api/farmer", tags=["Farmer"])
app.include_router(negotiation_router, prefix="/api/negotiation", tags=["Negotiation"])
app.include_router(simulation_router, prefix="/api/simulation", tags=["Simulation"])
app.include_router(warehouse_router, prefix="/api/warehouse", tags=["Warehouse"])

@app.get("/")
async def root():
    return {"message": "Welcome to AgriNegotiator API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
