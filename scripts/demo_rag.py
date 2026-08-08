import sys
import os

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.rag_service import rag_service
from backend.agents.graph_orchestrator import _build_rag_context


def run_demo():
    print("==================================================================")
    print("              FarmGenAI Standalone RAG Demonstration              ")
    print("==================================================================")
    print(f"Active Embedding Model: {rag_service.embedding_model.__class__.__name__}")
    model_name = "BAAI/bge-m3"
    if hasattr(rag_service.embedding_model, 'model_card_data') and rag_service.embedding_model.model_card_data is not None:
        model_name = getattr(rag_service.embedding_model.model_card_data, 'model_name', 'BAAI/bge-m3')
    print(f"Model ID: {model_name}")
    
    # Verify embedding dimension
    sample_emb = rag_service.embed_text("test query")
    print(f"Vector Space Dimension: {len(sample_emb)}")
    print("==================================================================")

    # DEMO 1 — Crop Knowledge
    print("\n[DEMO 1] Crop Knowledge RAG Query")
    print("Input Crop: Tomato")
    print("Query: 'irrigation and cultivation'")
    res1 = rag_service.query_crop_knowledge("irrigation and cultivation", crop="Tomato", n_results=1)
    if res1:
        doc = res1[0]
        text_preview = doc["text"][:300].replace("\n", " ").encode("ascii", errors="replace").decode("ascii")
        print(f"Status: SUCCESS")
        print(f"Retrieved Document Preview: {text_preview}...")
        print(f"Metadata: {doc['metadata']}")
    else:
        print("Status: FAILED (No document retrieved)")

    # DEMO 2 — Market Price
    print("\n[DEMO 2] Market Price RAG Query")
    print("Input Crop: Soyabean")
    print("Query: 'recent Soyabean mandi price Maharashtra'")
    res2 = rag_service.query_mandi_records("recent Soyabean mandi price Maharashtra", n_results=1, crop="Soyabean")
    docs = res2.get("documents", [[]])[0]
    metas = res2.get("metadatas", [[]])[0]
    if docs:
        text_preview = docs[0][:300].replace("\n", " ").encode("ascii", errors="replace").decode("ascii")
        meta = metas[0]
        print(f"Status: SUCCESS")
        print(f"Retrieved Market Evidence:")
        print(f"  - Crop: {meta.get('crop', 'Soyabean')}")
        print(f"  - Mandi/APMC: {meta.get('mandi', 'N/A')}")
        print(f"  - District: {meta.get('district', 'N/A')}")
        print(f"  - Date: {meta.get('date', 'N/A')}")
        print(f"  - Min Price: Rs. {meta.get('min_price', 0.0):.2f}/quintal")
        print(f"  - Max Price: Rs. {meta.get('max_price', 0.0):.2f}/quintal")
        print(f"  - Modal/Avg Price: Rs. {meta.get('modal_price', 0.0):.2f}/quintal")
        msp_val = meta.get("msp")
        msp_str = f"Rs. {msp_val:.2f}/quintal" if msp_val else "Not Available"
        print(f"  - MSP (2026-27): {msp_str}")
        print(f"  - Source File: {meta.get('source_file', 'N/A')}")
        print(f"Retrieved Document Text:\n  {text_preview}")
    else:
        print("Status: FAILED (No document retrieved)")

    # DEMO 3 — Historical Negotiation
    print("\n[DEMO 3] Historical Negotiation RAG Query")
    print("Query: 'previous successful Soyabean negotiation'")
    res3 = rag_service.query_strategies("previous successful Soyabean negotiation", n_results=1, crop="Soyabean", where_dict={"deal_status": "accepted"})
    docs3 = res3.get("documents", [[]])[0]
    metas3 = res3.get("metadatas", [[]])[0]
    if docs3:
        text_preview = docs3[0][:300].replace("\n", " ").encode("ascii", errors="replace").decode("ascii")
        meta = metas3[0]
        print(f"Status: SUCCESS")
        print(f"Retrieved Historical Negotiation:")
        print(f"  - Crop: {meta.get('crop', 'N/A')}")
        print(f"  - District: {meta.get('district', 'N/A')}")
        print(f"  - Deal Status: {meta.get('deal_status', 'N/A')}")
        print(f"  - Grade: {meta.get('grade', 'N/A')}")
        print(f"  - Date: {meta.get('date', 'N/A')}")
        print(f"Retrieved Document Text:\n  {text_preview}")
    else:
        print("Status: FAILED (No document retrieved)")

    # DEMO 4 — LangGraph RAG Context
    print("\n[DEMO 4] LangGraph RAG Context Build")
    print("Calling _build_rag_context(crop='Soyabean', location='Pune')...")
    context = _build_rag_context(crop="Soyabean", location="Pune")
    if context:
        print(f"Status: SUCCESS")
        print("Resulting RAG Context (First 1200 characters):")
        print("------------------------------------------------------------------")
        safe_context = context[:1200].encode("ascii", errors="replace").decode("ascii")
        print(safe_context)
        print("------------------------------------------------------------------")
    else:
        print("Status: FAILED (Returned empty context)")
    print("==================================================================")


if __name__ == "__main__":
    run_demo()
