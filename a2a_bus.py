import net_bootstrap  # noqa: F401 (must run before SSL/network imports)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import logging

# Logging (great for demo)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("A2A-Bus")

app = FastAPI(title="Philips A2A Message Bus")

# In-memory queues
subscribers = {}

class Message(BaseModel):
    sender: str
    receiver: str  # "all" for broadcast
    type: str
    payload: dict

# ROOT ENDPOINT (FIXES UI OFFLINE ISSUE)
@app.get("/")
async def root():
    return {"status": "A2A Bus Running"}

# HEALTH CHECK (optional but useful)
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "subscribers": list(subscribers.keys())
    }

# SUBSCRIBE (SAFE RECONNECT)
@app.post("/subscribe/{name}")
async def subscribe(name: str):
    if name not in subscribers:
        subscribers[name] = asyncio.Queue()
        logger.info(f"[BUS] {name} subscribed")
    else:
        logger.info(f"[BUS] {name} already subscribed (reusing queue)")

    return {"status": f"{name} connected"}

# POLL (CONSISTENT RESPONSE)
@app.get("/poll/{name}")
async def poll(name: str):
    if name not in subscribers:
        raise HTTPException(status_code=404, detail="Agent not subscribed")

    queue = subscribers[name]

    try:
        msg = await asyncio.wait_for(queue.get(), timeout=10.0)
        return msg

    except asyncio.TimeoutError:
        # IMPORTANT: return empty dict instead of random format
        return {}

# SEND (ROBUST ROUTING)
@app.post("/send")
async def send(msg: Message):
    logger.info(f"[BUS] {msg.sender} → {msg.receiver} ({msg.type})")

    # BROADCAST
    if msg.receiver == "all":
        count = 0
        for name, queue in subscribers.items():
            await queue.put(msg.dict())
            count += 1

        return {"status": "broadcast", "sent_to": count}

    # DIRECT MESSAGE
    if msg.receiver in subscribers:
        await subscribers[msg.receiver].put(msg.dict())
        return {"status": "delivered"}

    # RECEIVER NOT FOUND
    logger.warning(f"[BUS] Receiver {msg.receiver} not found")
    return {"status": "undelivered", "reason": "receiver_offline"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")