import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import net_bootstrap  # noqa: F401 (must run before SSL/network imports)

from fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn
import os
import json
import re

from dotenv import load_dotenv
load_dotenv()

mcp = FastMCP("AnalysisAgent")
app = FastAPI()

model = None


try:
    
    import google.generativeai as genai  # type: ignore
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash-lite")
except Exception:
    model = None

def safe_json_parse(text):
    try:
        # Cleanup markdown formatting if LLM includes it
        text = re.sub(r'```json\n?|```', '', text)
        return json.loads(text)
    except:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        return json.loads(match.group()) if match else {"risk": "UNKNOWN", "reason": text}

@mcp.tool()
def analyze_vitals(heart_rate: int, spo2: int):
    """Analyzes patient vitals and returns a risk assessment."""
    if spo2 < 85:
        return {"risk": "CRITICAL", "reason": "Severely low SpO2"}

    prompt = f"Analyze vitals: HR {heart_rate}, SpO2 {spo2}. Return JSON: {{'risk': 'HIGH|MEDIUM|NORMAL', 'reason': '...'}}"
    
    try:
        if model is None:
            raise RuntimeError("Gemini unavailable")
        response = model.generate_content(prompt)
        return safe_json_parse(response.text)
    except Exception:
        return {"risk": "HIGH", "reason": "Analysis Error - Fallback to High Alert"}

@app.post("/tools/analyze_vitals")
async def analyze_api(data: dict):
    return analyze_vitals(data["heart_rate"], data["spo2"])

@app.get("/mcp/tools")
async def list_tools():
    return {
        "agent": "AnalysisAgent",
        "tools": [
            {
                "name": "analyze_vitals",
                "description": "Analyze vitals and return risk level",
                "input_schema": {
                    "heart_rate": "int",
                    "spo2": "int"
                }
            }
        ]
    }


if __name__ == "__main__":
    uvicorn.run(app, port=9002, log_level="warning")















