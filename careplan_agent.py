from dotenv import load_dotenv
load_dotenv()

from fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn
import google.generativeai as genai
import os
import json
import re

mcp = FastMCP("CarePlanAgent")
app = FastAPI()

# Gemini setup
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-lite")

history = []


# Robust JSON parser
def safe_json_parse(text):
    try:
        return json.loads(text)
    except:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return {
        "action": "MONITOR",
        "plan": text
    }


@mcp.tool()
def plan(input_data: dict):
    analysis = input_data["analysis"]
    vitals = input_data["vitals"]

    history.append(analysis.get("risk", "UNKNOWN"))
    recent = history[-3:]

    # --- HARD SAFETY RULE ---
    if vitals["spo2"] < 85:
        return {
            "action": "CRITICAL",
            "plan": "Immediate ICU escalation",
            "source": "RULE_OVERRIDE"
        }

    prompt = f"""
    You are a clinical care planning assistant.

    Patient vitals:
    {vitals}

    Risk assessment:
    {analysis}

    Recent trend:
    {recent}

    Suggest care actions.

    Return ONLY valid JSON:
    {{
        "action": "CRITICAL | ESCALATE | ALERT | MONITOR | STABLE",
        "plan": "clear actionable instruction"
    }}
    """

    try:
        response = model.generate_content(prompt)
        text = response.text

        llm_output = safe_json_parse(text)

    except Exception as e:
        print("[Gemini ERROR]", e)
        llm_output = {"action": "MONITOR", "plan": "Fallback monitoring"}

    # --- GUARDRAILS ---

    # Prevent unsafe downgrade
    if analysis.get("risk") == "HIGH" and llm_output.get("action") == "STABLE":
        llm_output["action"] = "ALERT"
        llm_output["plan"] = "Adjusted: maintain monitoring due to high risk"

    # Escalate repeated HIGH
    if recent.count("HIGH") >= 2:
        llm_output["action"] = "ESCALATE"
        llm_output["plan"] = "Repeated high-risk → doctor intervention required"

    llm_output["source"] = "LLM+RULES"
    return llm_output


# HTTP endpoint
@app.post("/tools/plan")
async def plan_api(input_data: dict):
    return plan(input_data)

@app.get("/mcp/tools")
async def list_tools():
    return {
        "agent": "CarePlanAgent",
        "tools": [
            {
                "name": "plan",
                "description": "Generate adaptive care plan",
                "input_schema": {
                    "vitals": "dict",
                    "analysis": "dict"
                }
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, port=9003)


