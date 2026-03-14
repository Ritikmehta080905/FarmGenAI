import json
from llm.llm_router import ask_llm
import os


def farmer_decision(min_price, buyer_offer, spoilage_days):
    with open('llm/prompts/farmer_prompt.txt', 'r') as f:
        prompt_template = f.read()
    
    prompt = prompt_template.format(
        min_price=min_price,
        buyer_offer=buyer_offer,
        spoilage_days=spoilage_days
    )
    
    response = ask_llm(prompt)
    
    # Debug: print raw response
    if os.getenv("DEBUG_LLM", "false").lower() == "true":
        print(f"Raw LLM Response for farmer_decision:\n{response}\n")
    
    # Parse the response
    lines = response.strip().split('\n')
    decision = None
    new_price = None
    reason = None
    for line in lines:
        line = line.strip()
        if line.startswith('Decision:'):
            dec = line.split(':', 1)[1].strip()
            # Map numbers to text
            if dec == '1' or 'Accept' in dec:
                decision = "Accept offer"
            elif dec == '2' or 'Counter' in dec:
                decision = "Counter offer"
            elif dec == '3' or 'Store' in dec:
                decision = "Store in warehouse"
            elif dec == '4' or 'Sell to processor' in dec:
                decision = "Sell to processor"
            else:
                decision = dec
        elif 'New Price:' in line or 'Price:' in line:
            price_str = line.split(':', 1)[1].strip()
            if price_str not in ['N/A', 'n/a', 'NA', '']:
                # Extract number from string like "₹18/kg" or "18"
                import re
                match = re.search(r'(\d+)', price_str.replace('₹', '').replace('â‚¹', ''))
                if match:
                    new_price = int(match.group(1))
                else:
                    new_price = None
        elif 'Reason:' in line:
            reason = line.split(':', 1)[1].strip()
    
    return {
        'decision': decision,
        'new_price': new_price,
        'reason': reason
    }


def transport_decision(min_fee, client_offer, distance, spoilage_days):
    with open('llm/prompts/transport_prompt.txt', 'r') as f:
        prompt_template = f.read()
    
    prompt = prompt_template.format(
        min_fee=min_fee,
        client_offer=client_offer,
        distance=distance,
        spoilage_days=spoilage_days
    )
    
    response = ask_llm(prompt)
    
    # Parse the response
    lines = response.strip().split('\n')
    decision = None
    new_fee = None
    reason = None
    for line in lines:
        if line.startswith('Decision:'):
            decision = line.split(':', 1)[1].strip()
        elif line.startswith('New Fee:'):
            fee_str = line.split(':', 1)[1].strip()
            if fee_str not in ['N/A', 'n/a', 'NA']:
                try:
                    new_fee = int(fee_str.replace('₹', '').strip())
                except:
                    new_fee = None
        elif line.startswith('Reason:'):
            reason = line.split(':', 1)[1].strip()
    
def buyer_decision(max_price, farmer_ask, spoilage_days):
    with open('llm/prompts/buyer_prompt.txt', 'r') as f:
        prompt_template = f.read()
    
    prompt = prompt_template.format(
        max_price=max_price,
        farmer_ask=farmer_ask,
        spoilage_days=spoilage_days
    )
    
    response = ask_llm(prompt)
    
    # Parse the response
    lines = response.strip().split('\n')
    decision = None
    new_price = None
    reason = None
    for line in lines:
        line = line.strip()
        if line.startswith('Decision:'):
            dec = line.split(':', 1)[1].strip()
            # Map numbers to text
            if dec == '1' or 'Accept' in dec:
                decision = "Accept offer"
            elif dec == '2' or 'Reject' in dec:
                decision = "Reject offer"
            elif dec == '3' or 'Counter' in dec:
                decision = "Counter offer"
            else:
                decision = dec
        elif 'New Price:' in line or 'Price:' in line:
            price_str = line.split(':', 1)[1].strip()
            if price_str not in ['N/A', 'n/a', 'NA', '']:
                # Extract number from string like "₹18/kg" or "18"
                import re
                match = re.search(r'(\d+)', price_str.replace('₹', '').replace('â‚¹', ''))
                if match:
                    new_price = int(match.group(1))
                else:
                    new_price = None
        elif 'Reason:' in line:
            reason = line.split(':', 1)[1].strip()
    
    return {
        'decision': decision,
        'new_price': new_price,
        'reason': reason
    }


def processor_decision(demand_price, offered_price, quantity, spoilage_days):
    with open('llm/prompts/processor_prompt.txt', 'r') as f:
        prompt_template = f.read()
    
    prompt = prompt_template.format(
        demand_price=demand_price,
        offered_price=offered_price,
        quantity=quantity,
        spoilage_days=spoilage_days
    )
    
    response = ask_llm(prompt)
    
    # Parse the response
    lines = response.strip().split('\n')
    decision = None
    reason = None
    for line in lines:
        line = line.strip()
        if line.startswith('Decision:'):
            dec = line.split(':', 1)[1].strip()
            # Map numbers to text
            if dec == '1' or 'Buy' in dec:
                decision = "Buy"
            elif dec == '2' or 'Skip' in dec:
                decision = "Skip"
            else:
                decision = dec
        elif 'Reason:' in line:
            reason = line.split(':', 1)[1].strip()
    
    return {
        'decision': decision,
        'reason': reason
    }


def warehouse_decision(storage_cost, spoilage_days, market_price):
    with open('llm/prompts/warehouse_prompt.txt', 'r') as f:
        prompt_template = f.read()
    
    prompt = prompt_template.format(
        storage_cost=storage_cost,
        spoilage_days=spoilage_days,
        market_price=market_price
    )
    
    response = ask_llm(prompt)
    
    # Parse the response
    lines = response.strip().split('\n')
    decision = None
    reason = None
    for line in lines:
        line = line.strip()
        if line.startswith('Decision:'):
            dec = line.split(':', 1)[1].strip()
            # Map numbers to text
            if dec == '1' or 'Store' in dec:
                decision = "Store"
            elif dec == '2' or 'Sell fast' in dec:
                decision = "Sell fast"
            else:
                decision = dec
        elif 'Reason:' in line:
            reason = line.split(':', 1)[1].strip()
    
    return {
        'decision': decision,
        'reason': reason
    }

    min_price = 18
    buyer_offer = 16
    spoilage_days = 3

    print("Buyer initial offer:", buyer_offer)

    for round in range(3):

        result = farmer_decision(min_price, buyer_offer, spoilage_days)

        decision = result['decision']
        new_price = result['new_price']
        reason = result['reason']

        print(f"\nFarmer decision: {decision}")
        if new_price:
            print(f"New Price: ₹{new_price}")
        print(f"Reason: {reason}")

        if decision == "Accept offer":
            print("Deal accepted at price:", buyer_offer)
            return

        elif decision == "Store in warehouse":
            print("Farmer chooses to store in warehouse.")
            return

        elif decision == "Sell to processor":
            print("Farmer chooses to sell to processor.")
            return

        elif decision == "Counter offer":
            if new_price:
                buyer_offer = new_price
                print("Buyer considers the counter offer.")
            else:
                print("No new price provided.")
                return

    print("\nNegotiation ended.")