from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import logging

# Set up logging so you can show the interviewers the live message flow
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("A2A-Bus")

app = FastAPI(title="Philips A2A Message Bus")

# In-memory storage for queues
subscribers = {}

class Message(BaseModel):
    sender: str
    receiver: str # Use "all" for broadcast
    type: str     # e.g., "ALERT", "INFO", "CRITICAL"
    payload: dict

@app.post("/subscribe/{name}")
async def subscribe(name: str):
    subscribers[name] = asyncio.Queue()
    logger.info(f"Agent '{name}' connected to the bus.")
    return {"status": f"Agent {name} subscribed successfully"}

@app.get("/poll/{name}")
async def poll(name: str):
    if name not in subscribers:
        # Instead of empty {}, return a clear error
        raise HTTPException(status_code=404, detail="Agent not subscribed")

    queue = subscribers[name]
    try:
        # Wait for a message for 10 seconds
        msg = await asyncio.wait_for(queue.get(), timeout=10.0)
        return msg
    except asyncio.TimeoutError:
        return {"status": "timeout", "msg": None}

@app.post("/send")
async def send(msg: Message):
    logger.info(f"Routing message from {msg.sender} to {msg.receiver}")
    
    # Broadcast Logic (True A2A)
    if msg.receiver == "all":
        for name, queue in subscribers.items():
            await queue.put(msg.dict())
        return {"status": "broadcast_sent", "count": len(subscribers)}

    # Point-to-Point Logic
    if msg.receiver in subscribers:
        await subscribers[msg.receiver].put(msg.dict())
        return {"status": "delivered"}
    
    logger.warning(f"Receiver {msg.receiver} not found on bus.")
    return {"status": "undelivered", "reason": "receiver_offline"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


