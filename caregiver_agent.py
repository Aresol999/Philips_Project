import asyncio
import httpx

BUS = "http://127.0.0.1:8000"

async def run():
    async with httpx.AsyncClient(timeout=None) as client:
        # Subscribe to A2A bus
        try:
            await client.post(f"{BUS}/subscribe/Caregiver")
            print("[Caregiver] Subscribed to A2A bus")
        except Exception as e:
            print("[Caregiver] Failed to connect to bus:", e)
            return

        # Poll loop
        while True:
            try:
                response = await client.get(f"{BUS}/poll/Caregiver")
                msg = response.json()

                if msg:
                    print("\n[CAREGIVER RECEIVED]")
                    print(f"From: {msg.get('sender')}")
                    print(f"Type: {msg.get('type')}")
                    print(f"Payload: {msg.get('payload')}")

                    # Simulated action
                    print("[Caregiver Action] Executing care instruction...")

            except httpx.ReadTimeout:
                pass
            except Exception as e:
                print("[Caregiver] Error:", e)

            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run())