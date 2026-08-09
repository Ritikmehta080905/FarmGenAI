import re

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract lifespan
lifespan_match = re.search(r'(@asynccontextmanager.*?yield.*?\n)', content, flags=re.DOTALL)
if lifespan_match:
    lifespan_str = lifespan_match.group(1)
    # Remove it from where it is
    content = content.replace(lifespan_str, '')
    
    # Add it above app = FastAPI(
    content = content.replace('app = FastAPI(', f"{lifespan_str}\n\napp = FastAPI(")
    
    with open('backend/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
