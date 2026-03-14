from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.auth_routes import router as auth_router
from backend.routes.farmer_routes import router as farmer_router
from backend.routes.buyer_routes import router as buyer_router
from backend.routes.negotiation_routes import router as negotiation_router
from backend.routes.warehouse_routes import router as warehouse_router
from backend.routes.simulation_routes import router as simulation_router
from backend.routes.history_routes import router as history_router

app = FastAPI(
    title="AgriNegotiator API",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(farmer_router)
app.include_router(buyer_router)
app.include_router(negotiation_router)
app.include_router(warehouse_router)
app.include_router(simulation_router)
app.include_router(history_router)


@app.get("/")
def root():
    return {
        "message": "AgriNegotiator API is running",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "API running"}