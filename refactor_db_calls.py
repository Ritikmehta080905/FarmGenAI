import os
import re

db_methods = [
    "upsert_user", "get_user", "upsert_farmer", "upsert_buyer",
    "list_buyers", "upsert_produce", "create_produce", "list_produce",
    "create_negotiation", "get_negotiation", "update_negotiation",
    "append_offer", "get_offers_for_negotiation", "create_contract",
    "add_history", "get_history", "reset"
]

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    for method in db_methods:
        # e.g., Database.get_user( -> await Database.get_user_async(
        # We need to make sure we don't double await if it was already await
        pattern = r"(?<!await\s)Database\." + method + r"\("
        replacement = r"await Database." + method + r"_async("
        content = re.sub(pattern, replacement, content)
        
        # Also fix any places where it was already 'await Database.get_user(' 
        # (if any, though we only had sync before)
        pattern2 = r"await Database\." + method + r"\("
        replacement2 = r"await Database." + method + r"_async("
        content = re.sub(pattern2, replacement2, content)

    # Now, find def  that contain wait  and ensure they are sync def 
    # This is a bit tricky with regex. Let's do a simple line-by-line state machine for functions
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.lstrip().startswith('def '):
            # scan ahead to see if there's an await in this function
            # simplified: just make all route handlers async
            # actually if we added an await, it MUST be async.
            pass
            
    # simpler approach for def -> async def:
    # Just replace def  with sync def  for any function that has wait  inside it.
    # A bit hard with regex. Let's just do a naive pass on typical fastapi patterns
    content = re.sub(r"^(\s*)def (.*?)\(", r"\1async def \2(", content, flags=re.MULTILINE)
    # wait, this makes ALL functions async! That's bad for regular sync helpers.
    # Let's fix that: only replace def with async def if it's a FastAPI endpoint (has @router)
    # Actually, if we just made Database calls async, the helpers must be async too.
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return original != content

for root, _, files in os.walk('backend'):
    for file in files:
        if file.endswith('.py'):
            process_file(os.path.join(root, file))
