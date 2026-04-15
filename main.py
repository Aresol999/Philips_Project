import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import net_bootstrap  # noqa: F401 (must run before SSL/network imports)

import asyncio
import httpx
import os
import json
from dotenv import load_dotenv



from mcp_registry import MCPRegistry

# ---------------- SETUP ----------------
load_dotenv()



planner_model = None
try:
    import google.generativeai as genai  # type: ignore
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    # Use gemini-2.5-flash for stability during demo
    planner_model = genai.GenerativeModel("gemini-2.5-flash")
except Exception as _e:
    # Safe fallback: planner() already has deterministic fallback behavior.
    planner_model = None

BUS = "http://127.0.0.1:8000"

AGENTS = {
    "MonitoringAgent": "http://127.0.0.1:9001",
    "AnalysisAgent": "http://127.0.0.1:9002",
    "CarePlanAgent": "http://127.0.0.1:9003"
}

registry = MCPRegistry(AGENTS)

# ---------------- DYNAMIC HELPER: SCHEMA MAPPER ----------------
def map_context_to_schema(schema, context):
    payload = {}
    for param_name in schema.keys():
        # Priority 1: Direct match (The tool wants 'analysis', we have context['analysis'])
        if param_name in context:
            payload[param_name] = context[param_name]
        
        # Priority 2: Sub-key match (The tool wants 'heart_rate', we find it in context['vitals'])
        elif "vitals" in context and isinstance(context["vitals"], dict):
            if param_name in context["vitals"]:
                payload[param_name] = context["vitals"][param_name]
        
        # Priority 3: Analysis sub-key match
        elif "analysis" in context and isinstance(context["analysis"], dict):
            if param_name in context["analysis"]:
                payload[param_name] = context["analysis"][param_name]
                
    return payload

# ---------------- AUTONOMOUS PLANNER ----------------
async def planner(vitals, tools_metadata):
    tool_descriptions = {name: meta["description"] for name, meta in tools_metadata.items()}
    prompt = f"""
    You are an autonomous medical orchestrator.
    Vitals: {vitals}
    Tools: {tool_descriptions}

    Task: Create a JSON list of tool names to execute.
    - Stable vitals: ["analyze_vitals"]
    - Abnormal/Critical vitals: ["analyze_vitals", "plan"]
    
    Return ONLY JSON: ["tool1", "tool2"]
    """
    try:
        if planner_model is None:
            raise RuntimeError("Gemini unavailable")
        response = planner_model.generate_content(prompt)
        text = response.text
        return json.loads(text[text.find("["):text.rfind("]")+1])
    except:
        return ["analyze_vitals", "plan"]

# ---------------- MAIN EXECUTION LOOP ----------------
async def run():
    async with httpx.AsyncClient(timeout=None, trust_env=False) as client:
        print("=== PHILIPS AUTONOMOUS ORCHESTRATOR ===")
        await registry.discover_tools()
        tools_metadata = registry.list_tools()

        while True:
            vitals = await registry.call_tool(client, "get_vitals")
            if "error" in vitals:
                await asyncio.sleep(5); continue

            print(f"\n[1. Sensed Vitals] {vitals}")
            context = {"vitals": vitals}

            execution_plan = await planner(vitals, tools_metadata)
            print(f"[2. Plan] {' -> '.join(execution_plan)}")

            for tool_name in execution_plan:
                if tool_name not in tools_metadata: continue

                schema = tools_metadata[tool_name].get("input_schema", {})
                payload = map_context_to_schema(schema, context)
                
                print(f"[3. Executing {tool_name}]")
                result = await registry.call_tool(client, tool_name, payload)
                print(f"   ∟ Result: {result}")

                # Update context based on tool function
                if "analyze" in tool_name:
                    context["analysis"] = result
                elif "plan" in tool_name:
                    context["care_plan"] = result
                    
                    if isinstance(result, dict) and result.get("action") in ["CRITICAL", "ESCALATE"]:
                        alert = {"sender":"Orchestrator", "receiver":"all", "type":result["action"], "payload":result}
                        await client.post(f"{BUS}/send", json=alert)
                        print(f"!! [A2A Alert] Sent {result['action']} to clinical bus.")

            print("-" * 30)
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run())




