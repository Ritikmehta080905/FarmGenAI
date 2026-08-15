import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.services.rag_service import rag_service

async def ingest():
    print("Ingesting Knowledge Base...")
    rag_service.ingest_knowledge_base()
    
    print("Ingesting Mandi Prices and Negotiations...")
    rag_service.ingest_mandi_prices_and_negotiations()
    
    print("Chroma Ingestion Complete!")

if __name__ == "__main__":
    asyncio.run(ingest())
