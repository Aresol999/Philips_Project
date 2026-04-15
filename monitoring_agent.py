from fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn
import json

mcp = FastMCP("MonitoringAgent")
app = FastAPI()

# Load dataset
with open("vitals_patients.json", "r") as f:
    data = json.load(f)

index = 0

@mcp.tool()
def get_vitals():
    global index

    patient = data[index]
    index = (index + 1) % len(data)

    return {
        "time": patient.get("time", index),
        "patient_id": patient.get("patient_id"),
        "heart_rate": patient.get("heart_rate"),
        "spo2": patient.get("spo2")
    }

@app.post("/tools/get_vitals")
async def get_vitals_api():
    return get_vitals()

@app.get("/mcp/tools")
async def list_tools():
    return {
        "agent": "MonitoringAgent",
        "tools": [
            {
                "name": "get_vitals",
                "description": "Stream patient vitals over time",
                "input_schema": {}
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, port=9001, log_level="warning")