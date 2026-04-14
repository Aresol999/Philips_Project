from fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn
import google.generativeai as genai
import os
import json
import re

mcp = FastMCP("AnalysisAgent")
app = FastAPI()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash-lite") 

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
    uvicorn.run(app, port=9002)















