import asyncio
import httpx
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
import time

from mcp_registry import MCPRegistry

# ---------------- SETUP ----------------
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

planner_model = genai.GenerativeModel("gemini-2.5-flash-lite")

BUS = "http://127.0.0.1:8000"

# Agents (only entry points known — NOT tools)
AGENTS = {
    "MonitoringAgent": "http://127.0.0.1:9001",
    "AnalysisAgent": "http://127.0.0.1:9002",
    "CarePlanAgent": "http://127.0.0.1:9003"
}

registry = MCPRegistry(AGENTS)

# ---------------- PLANNER ----------------


''''''
async def planner(vitals, tools):
    tool_descriptions = {
        name: tools[name]["description"]
        for name in tools
    }

    prompt = f"""
    You are an autonomous medical orchestrator.

    Patient vitals:
    {vitals}

    Available tools:
    {tool_descriptions}

    Decide the sequence of tools to call.

    Return JSON:
    [
        {{"tool": "tool_name"}}
    ]
    """

    response = planner_model.generate_content(prompt)

    try:
        text = response.text
        start = text.find("[")
        end = text.rfind("]") + 1
        return json.loads(text[start:end])
    except:
        return [{"tool": "analyze_vitals"}, {"tool": "plan"}]


# ---------------- MAIN LOOP ----------------
async def run():
    async with httpx.AsyncClient(timeout=None) as client:

        print("=== MCP TOOL DISCOVERY SYSTEM ===")

        await registry.discover_tools()

        tools = registry.list_tools()
        print(f"[Discovered Tools] {list(tools.keys())}")

        while True:

            # Always start with vitals (discovered, not hardcoded)
            vitals = await registry.call_tool(client, "get_vitals")
            print(f"\n[Vitals] {vitals}")

            plan = await planner(vitals, tools)
            print(f"[Plan] {plan}")

            context = {"vitals": vitals}

            for step in plan:
                tool = step["tool"]

                # Context injection
                if tool == "analyze_vitals":
                    payload = context["vitals"]

                elif tool == "plan":
                    payload = {
                        "vitals": context["vitals"],
                        "analysis": context.get("analysis", {})
                    }
                else:
                    payload = {}

                result = await registry.call_tool(client, tool, payload)

                print(f"[Executed] {tool} → {result}")

                if tool == "analyze_vitals":
                    context["analysis"] = result

                elif tool == "plan":
                    context["care_plan"] = result

                    if result.get("action") in ["CRITICAL", "ESCALATE", "ALERT"]:
                        await client.post(f"{BUS}/send", json={
                            "sender": "ChiefResident",
                            "receiver": "all",
                            "type": result["action"],
                            "payload": result
                        })
                        print("[A2A] Alert broadcasted")

            await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(run())

    


