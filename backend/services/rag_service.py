"""
backend/services/rag_service.py

ChromaDB RAG vector search engine for regional mandi prices
and past agent negotiation strategy logs.
"""

import logging
from sentence_transformers import SentenceTransformer
import chromadb
from config.settings import CHROMA_URL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAGService")


class RAGService:
    """Vector database service utilizing ChromaDB and SentenceTransformers."""
    
    def __init__(self):
        # Initialize lightweight embeddings model
        logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.client = None
        self.mandi_collection = None
        self.strategies_collection = None
        import asyncio
        asyncio.create_task(self._init_client())

    async def _init_client(self):
        """Initialize Chroma client with failsafe fallbacks."""
        try:
            # Parse CHROMA_URL
            host = "localhost"
            port = 8001
            if "://" in CHROMA_URL:
                parts = CHROMA_URL.split("://")[1].split(":")
                host = parts[0]
                if len(parts) > 1:
                    port = int(parts[1])
                    
            self.client = chromadb.HttpClient(host=host, port=port)
            # Trigger a ping check
            self.client.heartbeat()
            logger.info(f"Successfully connected to external ChromaDB server at {host}:{port}.")
        except Exception as e:
            logger.warning(f"ChromaDB external client failed: {e}. Falling back to PersistentClient.")
            try:
                self.client = chromadb.PersistentClient(path="./node_storage/chroma_db")
            except Exception as ex:
                logger.error(f"Persistent local client failed: {ex}. Using temporary EphemeralClient.")
                self.client = chromadb.EphemeralClient()

        # Initialize indexing collections
        try:
            self.mandi_collection = self.client.get_or_create_collection(
                name="mandi_pricing_index",
                metadata={"description": "Regional mandi transaction records"}
            )
            self.strategies_collection = self.client.get_or_create_collection(
                name="strategies_index",
                metadata={"description": "Reflection agent strategy logs"}
            )
            logger.info("Chroma collections initialized successfully.")
        except Exception as e:
            logger.error(f"Error creating Chroma collections: {e}")

    def embed_text(self, text: str) -> list:
        """Encode text to vector space."""
        return self.embedding_model.encode(text).tolist()

    async def add_mandi_record(self, record_id: str, text: str, metadata: dict):
        """Insert regional Mandi transaction record into VDB."""
        if not self.mandi_collection:
            return
        vector = self.embed_text(text)
        self.mandi_collection.add(
            ids=[record_id],
            embeddings=[vector],
            documents=[text],
            metadatas=[metadata]
        )

    async def query_mandi_records(self, query_text: str, n_results: int = 3) -> dict:
        """Search Mandi database for similar market entries."""
        if not self.mandi_collection:
            return {}
        vector = self.embed_text(query_text)
        return self.mandi_collection.query(
            query_embeddings=[vector],
            n_results=n_results
        )

    async def add_strategy_log(self, log_id: str, text: str, metadata: dict):
        """Insert Reflection post-mortem logs for historical context."""
        if not self.strategies_collection:
            return
        vector = self.embed_text(text)
        self.strategies_collection.add(
            ids=[log_id],
            embeddings=[vector],
            documents=[text],
            metadatas=[metadata]
        )

    async def query_strategies(self, query_text: str, n_results: int = 3) -> dict:
        """Search strategy post-mortems for matching tactical cues."""
        if not self.strategies_collection:
            return {}
        vector = self.embed_text(query_text)
        return self.strategies_collection.query(
            query_embeddings=[vector],
            n_results=n_results
        )


# Singleton instance
rag_service = RAGService()
