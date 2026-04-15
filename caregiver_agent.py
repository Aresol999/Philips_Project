import net_bootstrap  # noqa: F401 (must run before SSL/network imports)

import asyncio
import httpx

BUS = "http://127.0.0.1:8000"

async def subscribe(client):
    while True:
        try:
            await client.post(f"{BUS}/subscribe/Caregiver")
            print("[Caregiver] Connected to A2A bus")
            break
        except Exception:
            print("[Caregiver] Waiting for bus...")
            await asyncio.sleep(2)

async def poll(client):
    while True:
        try:
            response = await client.get(f"{BUS}/poll/Caregiver")
            msg = response.json()

            if isinstance(msg, dict) and msg.get('payload'):
                print("\n[CAREGIVER RECEIVED]")
                print(f"From: {msg.get('sender')}")
                print(f"Type: {msg.get('type')}")
                print(f"Payload: {msg.get('payload')}")

                print("[Caregiver Action] Executing care instruction...")

        except Exception as e:
            print("[Caregiver] Poll error:", e)

        await asyncio.sleep(1)

async def run():
    async with httpx.AsyncClient(timeout=None, trust_env=False) as client:
        await subscribe(client)
        await poll(client)

if __name__ == "__main__":
    asyncio.run(run())