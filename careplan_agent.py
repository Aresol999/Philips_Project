import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import net_bootstrap  # noqa: F401 (must run before SSL/network imports)

from dotenv import load_dotenv
load_dotenv()



from fastapi import FastAPI, Request
import uvicorn
import os
import json
import re



app = FastAPI()
model = None
try:
    import google.generativeai as genai  # type: ignore
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash")
except Exception:
    model = None

history = []

def safe_json_parse(text):
    try:
        return json.loads(text)
    except:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        return json.loads(match.group()) if match else {"action": "MONITOR", "plan": text}

def plan_logic(input_data: dict):
    # FALLBACK LOGIC: If 'analysis' key is missing, treat the whole input as the analysis
    analysis = input_data.get("analysis", input_data)
    vitals = input_data.get("vitals", {})

    # Maintain clinical history
    history.append(analysis.get("risk", "UNKNOWN"))
    recent = history[-3:]

    # --- HARD SAFETY RULE (Deterministic) ---
    if vitals.get("spo2", 100) < 85:
        return {"action": "CRITICAL", "plan": "SPO2 Danger: Immediate ICU escalation", "source": "SAFETY_RULE"}

    prompt = f"""
    You are a clinical care assistant. 
    Vitals: {vitals}
    Risk Analysis: {analysis}
    Trend: {recent}
    Return JSON: {{"action": "CRITICAL|ESCALATE|ALERT|MONITOR", "plan": "..."}}
    """

    try:
        if model is None:
            raise RuntimeError("Gemini unavailable")
        response = model.generate_content(prompt)
        llm_output = safe_json_parse(response.text)
    except Exception as e:
        llm_output = {"action": "MONITOR", "plan": "Fallback monitoring active"}

    # Guardrail: Prevent ignoring high risk
    if analysis.get("risk") == "HIGH" and llm_output.get("action") == "STABLE":
        llm_output["action"] = "ALERT"
    
    llm_output["source"] = "LLM+RULES"
    return llm_output

@app.post("/tools/plan")
async def plan_api(request: Request):
    data = await request.json()
    return plan_logic(data)

@app.get("/mcp/tools")
async def list_tools():
    return {
        "agent": "CarePlanAgent",
        "tools": [{
            "name": "plan",
            "description": "Generates clinical care instructions",
            "input_schema": {
                "vitals": "object",
                "analysis": "object"
            }
        }]
    }

if __name__ == "__main__":
    uvicorn.run(app, port=9003, log_level="warning")



