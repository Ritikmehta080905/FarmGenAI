"""
backend/services/rag_service.py

Advanced ChromaDB RAG vector search engine for AgriNegotiator.
Implements the 13 specialized collections and Hybrid Search concepts.
Uses BAAI/bge-m3 for dense vector embedding.
"""

import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import chromadb

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAGService")

# Using BAAI/bge-m3 for multilingual robust embedding (English, Hindi, Marathi)
EMBEDDING_MODEL = "BAAI/bge-m3"

COLLECTION_NAMES = [
    "crop_knowledge",
    "historical_negotiations",
    "government_rules",
    "market_prices",
    "weather_knowledge",
    "warehouse_knowledge",
    "transport_knowledge",
    "farmer_profiles",
    "buyer_profiles",
    "reflection_memory",
    "trust_memory",
    "learning_memory",
    "recommendations",
]


class RAGService:
    """Vector database service utilizing ChromaDB and BAAI/bge-m3."""

    def __init__(self):
        logger.info(f"Loading SentenceTransformer model '{EMBEDDING_MODEL}'...")
        try:
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        except Exception as e:
            logger.warning(f"Failed to load {EMBEDDING_MODEL}. Falling back to default: {e}")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
        self.client = None
        self.collections: dict = {}
        self._init_client()

    def _init_client(self):
        """Initialize Chroma client with persistent local storage for production."""
        try:
            self.client = chromadb.PersistentClient(path="./node_storage/chroma_db_v2")
            logger.info("Connected to local PersistentClient for ChromaDB.")
        except Exception as ex:
            logger.error(f"Persistent local client failed: {ex}. Using EphemeralClient.")
            self.client = chromadb.EphemeralClient()

        # Initialize all 13 collections
        for name in COLLECTION_NAMES:
            try:
                col = self.client.get_or_create_collection(
                    name=name,
                    metadata={"description": f"AgriNegotiator {name} vector store (bge-m3)"}
                )
                self.collections[name] = col
            except Exception as e:
                logger.error(f"Error creating collection '{name}': {e}")

        logger.info(f"Initialized {len(self.collections)} ChromaDB collections.")

    def embed_text(self, text: str) -> list:
        """Encode text to vector space."""
        return self.embedding_model.encode(text).tolist()

    def add_document(self, collection_name: str, doc_id: str, text: str, metadata: dict):
        """Insert document into named vector collection with metadata validation."""
        col = self.collections.get(collection_name)
        if not col:
            logger.error(f"Collection {collection_name} not found.")
            return
            
        # Ensure timestamp exists for stale knowledge filtering
        if "timestamp" not in metadata:
            import time
            metadata["timestamp"] = int(time.time())
            
        vector = self.embed_text(text)
        col.add(ids=[doc_id], embeddings=[vector], documents=[text], metadatas=[metadata])
        logger.info(f"Added doc {doc_id} to {collection_name}")

    def query_collection(self, collection_name: str, query_text: str, n_results: int = 3, where: Optional[Dict] = None) -> dict:
        """Search a specific vector collection with optional metadata filtering."""
        col = self.collections.get(collection_name)
        if not col:
            return {}
            
        vector = self.embed_text(query_text)
        
        # Example where filter: {"$and": [{"crop": "Tomato"}, {"timestamp": {"$gt": 1700000000}}]}
        if where:
            return col.query(query_embeddings=[vector], n_results=n_results, where=where)
        else:
            return col.query(query_embeddings=[vector], n_results=n_results)


# Singleton instance
rag_service = RAGService()
