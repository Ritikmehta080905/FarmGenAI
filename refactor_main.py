import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add lifespan import and p2p router
content = re.sub(r'from fastapi import BackgroundTasks, FastAPI, WebSocket, WebSocketDisconnect, Depends, Request', 
                 'from fastapi import BackgroundTasks, FastAPI, WebSocket, WebSocketDisconnect, Depends, Request\nfrom contextlib import asynccontextmanager', content)

content = re.sub(r'from \.routes\.buyer_req_routes import router as buyer_req_router',
                 'from .routes.buyer_req_routes import router as buyer_req_router\nfrom .routes.p2p_routes import router as p2p_router', content)

# 2. Replace @app.on_event("startup") with lifespan
lifespan_str = '''@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("dYs? API GLOBAL STARTUP INITIATED...")
    await init_db()
    
    from backend.services.negotiation_service import service as negotiation_service
    await negotiation_service.ensure_default_buyers()
    await negotiation_service.ensure_default_farmers_and_produce()
    
    await bootstrap_peer_network()
    
    global redis_client
    try:
        redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("Connected to Redis successfully.")
        asyncio.create_task(redis_pubsub_listener())
    except Exception as e:
        logger.warning(f"s? Redis not reachable ({e}). WebSocket updates will fall back to direct memory updates.")
        redis_client = None
    yield
    # Cleanup here if necessary
'''
content = re.sub(r'@app\.on_event\("startup"\)\s*async def on_startup\(\):.*?(?=#)', lifespan_str, content, flags=re.DOTALL | re.MULTILINE)

# 3. Add lifespan to FastAPI()
content = re.sub(r'app = FastAPI\(\n\s*title="AgriNegotiator API"', 'app = FastAPI(\n    title="AgriNegotiator API",\n    lifespan=lifespan', content)

# 4. Remove the old P2P routes
p2p_routes_pattern = r'#  Decentralized P2P API .*?return {"status": "success", "block": block, "negotiation_id": neg_id}'
content = re.sub(p2p_routes_pattern, '', content, flags=re.DOTALL)

# 5. Add p2p router to app
content = re.sub(r'app\.include_router\(buyer_req_router\)', 'app.include_router(buyer_req_router)\napp.include_router(p2p_router, prefix="/api")', content)

# 6. Replace print( with logger.info( in main.py
content = re.sub(r'(?<!_)print\(', 'logger.info(', content)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
