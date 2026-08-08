import asyncio
import redis.asyncio as redis

async def main():
    r = redis.Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    
    # Delete the old consumer group so the new worker starts fresh
    try:
        await r.xgroup_destroy("agri:negotiation:jobs", "worker_group")
        print("Deleted old consumer group")
    except Exception as e:
        print(f"Could not delete group: {e}")
    
    # Recreate it starting from the beginning (id=0) so it reprocesses ALL jobs
    try:
        await r.xgroup_create("agri:negotiation:jobs", "worker_group", id="0", mkstream=True)
        print("Recreated consumer group from id=0")
    except Exception as e:
        print(f"Could not create group: {e}")
    
    # Check how many messages are pending
    info = await r.xinfo_stream("agri:negotiation:jobs")
    length = info.get("length", 0)
    print(f"Stream length: {length}")

asyncio.run(main())
