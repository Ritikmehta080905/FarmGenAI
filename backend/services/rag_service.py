"""
backend/services/rag_service.py

ChromaDB RAG vector search engine for regional mandi prices, weather,
government schemes, trust history, and agent strategy logs.
Implements 9 specialized vector collections per system architecture specification.
"""

import logging
from sentence_transformers import SentenceTransformer
import chromadb
from config.settings import CHROMA_URL, EMBEDDING_MODEL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAGService")


COLLECTION_NAMES = [
    "market_prices",
    "historical_negotiations",
    "weather",
    "government_schemes",
    "trust_memory",
    "reflection_memory",
    "warehouse_data",
    "transport_data",
    "recommendations",
]


class RAGService:
    """Vector database service utilizing ChromaDB and SentenceTransformers."""

    def __init__(self):
        logger.info(f"Loading SentenceTransformer model '{EMBEDDING_MODEL}'...")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self.client = None
        self.collections: dict = {}
        self._init_client()

    def _init_client(self):
        """Initialize Chroma client with failsafe fallbacks."""
        try:
            host = "localhost"
            port = 8001
            if "://" in CHROMA_URL:
                parts = CHROMA_URL.split("://")[1].split(":")
                host = parts[0]
                if len(parts) > 1:
                    port = int(parts[1])

            self.client = chromadb.HttpClient(host=host, port=port)
            self.client.heartbeat()
            logger.info(f"Connected to external ChromaDB server at {host}:{port}.")
        except Exception as e:
            logger.warning(f"ChromaDB external client failed: {e}. Falling back to PersistentClient.")
            try:
                self.client = chromadb.PersistentClient(path="./node_storage/chroma_db")
            except Exception as ex:
                logger.error(f"Persistent local client failed: {ex}. Using EphemeralClient.")
                self.client = chromadb.EphemeralClient()

        # Initialize all 9 collections
        for name in COLLECTION_NAMES:
            try:
                col = self.client.get_or_create_collection(
                    name=name,
                    metadata={"description": f"AgriNegotiator {name} vector store"}
                )
                self.collections[name] = col
            except Exception as e:
                logger.error(f"Error creating collection '{name}': {e}")

        # Aliases for backward compatibility
        self.mandi_collection = self.collections.get("market_prices")
        self.strategies_collection = self.collections.get("reflection_memory")
        logger.info(f"Initialized {len(self.collections)} ChromaDB collections.")

    def embed_text(self, text: str) -> list:
        """Encode text to vector space."""
        return self.embedding_model.encode(text).tolist()

    def add_document(self, collection_name: str, doc_id: str, text: str, metadata: dict):
        """Insert document into named vector collection."""
        col = self.collections.get(collection_name)
        if not col:
            return
        vector = self.embed_text(text)
        col.add(ids=[doc_id], embeddings=[vector], documents=[text], metadatas=[metadata])

    def query_collection(self, collection_name: str, query_text: str, n_results: int = 3) -> dict:
        """Search a specific vector collection by semantic similarity."""
        col = self.collections.get(collection_name)
        if not col:
            return {}
        vector = self.embed_text(query_text)
        return col.query(query_embeddings=[vector], n_results=n_results)

    # Legacy helper wrappers
    def add_mandi_record(self, record_id: str, text: str, metadata: dict):
        self.add_document("market_prices", record_id, text, metadata)

    def query_mandi_records(self, query_text: str, n_results: int = 3) -> dict:
        return self.query_collection("market_prices", query_text, n_results)

    def add_strategy_log(self, log_id: str, text: str, metadata: dict):
        self.add_document("reflection_memory", log_id, text, metadata)

    def query_strategies(self, query_text: str, n_results: int = 3) -> dict:
        return self.query_collection("reflection_memory", query_text, n_results)


# Singleton instance
rag_service = RAGService()
