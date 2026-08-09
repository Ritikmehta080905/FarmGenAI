import os
import sys

# Ensure backend modules are importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import Database
from backend.services.rag_service import rag_service
from backend.agents.graph_orchestrator import _build_rag_context

def print_header(title: str):
    print("\n" + "=" * 60)
    print(f" {title.center(58)} ")
    print("=" * 60)

def main():
    print_header("FarmGenAI Interactive RAG & DB Verification Demo")
    print("This script queries the active relational tables and ChromaDB vector stores.")
    print("Ensure database seeding is complete before running.")

    # 1. User Input Prompts
    crop_input = input("\nEnter Crop Name [Onion]: ").strip() or "Onion"
    crop = crop_input.capitalize()
    if crop.lower() in ["soybean", "soyabean"]:
        crop = "Soyabean"
    
    location_input = input("Enter District/Location [Pune]: ").strip() or "Pune"
    location = location_input.capitalize()
    
    query = input("Enter Search Query [cultivation and irrigation]: ").strip() or "cultivation and irrigation"

    print("\nProcessing request...")

    print("\n💡 NOTE FOR TEAMMATES: Why do negotiation agents use cultivation and irrigation guidelines?")
    print("   During a negotiation, the agents debate crop quality (moisture, shelf-life, grade).")
    print("   If guidelines show that the crop is highly perishable or has high moisture, the buyer")
    print("   agent uses this to demand discounts, while the farmer agent adjusts their concessions based")
    print("   on the crop's storage/shelf-life limit.")

    # 2. Database Lookups
    print_header("1. Relational Database Seeding Results")
    try:
        msp = Database.get_msp_price(crop)
        if msp:
            print(f"✔️ MSP Price found: ₹{msp:.2f}/quintal (₹{msp/100:.2f}/kg) for {crop}.")
        else:
            print(f"❌ No MSP entry found for crop '{crop}'.")

        mappings = Database.get_market_mappings(location)
        if mappings:
            markets_str = ", ".join([m["market_name"] for m in mappings])
            print(f"✔️ Associated wholesale APMCs for {location} district: {markets_str}.")
        else:
            print(f"❌ No wholesale APMC mappings found for district '{location}'.")

        quality = Database.get_crop_quality_reference(crop)
        if quality:
            print(f"✔️ Crop Quality Standards loaded ({len(quality)} grades found).")
            for q in quality:
                print(f"  - Grade {q['grade']} {q['variety']}: Size >= {q['min_size_mm']}mm, Max Moisture {q['max_moisture_pct']}%")
        else:
            print(f"❌ No quality standards found for crop '{crop}'.")
    except Exception as e:
        print(f"⚠️ Error querying relational DB: {e}")

    # 3. Vector Database Retrieval
    print_header("2. ChromaDB Semantic Vector Searches")
    try:
        # A. Crop Knowledge
        print(f"\n🔍 Querying crop_knowledge for '{query}' (Filtered by Crop='{crop}'):")
        crop_results = rag_service.query_crop_knowledge(query, crop=crop, n_results=2)
        if crop_results:
            for idx, res in enumerate(crop_results):
                print(f"  [{idx + 1}] Source: {res['metadata'].get('source', 'Unknown')}")
                text_snippet = res['text'][:200].replace('\n', ' ')
                print(f"      Snippet: {text_snippet}...")
        else:
            print("  ❌ No matching agronomic guidelines found.")

        # B. Mandi Prices
        print(f"\n🔍 Querying market_prices for recent transactions near '{location}':")
        mandi_results = rag_service.query_mandi_records(f"{crop} {location}", n_results=2)
        if mandi_results and mandi_results.get("documents"):
            docs = mandi_results["documents"][0]
            if docs:
                for idx, doc in enumerate(docs):
                    print(f"  [{idx + 1}] {doc}")
            else:
                print("  ❌ No matching transactions found.")
        else:
            print("  ❌ No matching transactions found.")

        # C. Government Schemes
        print(f"\n🔍 Querying government_schemes for 'insurance claim procedure':")
        scheme_results = rag_service.query_government_schemes("insurance claim procedure", n_results=1)
        if scheme_results:
            for idx, res in enumerate(scheme_results):
                print(f"  [{idx + 1}] Source: {res['metadata'].get('source', 'Unknown')}")
                text_snippet = res['text'][:200].replace('\n', ' ')
                print(f"      Snippet: {text_snippet}...")
        else:
            print("  ❌ No matching schemes found.")
    except Exception as e:
        print(f"⚠️ Error querying vector store: {e}")

    # 4. Synthesized Context Hook (Agent Input)
    print_header("3. Synthesized Context Context (Sent to Agents)")
    try:
        context = _build_rag_context(crop, location)
        print(context)
    except Exception as e:
        print(f"⚠️ Error building context profile: {e}")

    print("=" * 60)
    print(" Demo complete! ".center(60, "="))

if __name__ == "__main__":
    main()
