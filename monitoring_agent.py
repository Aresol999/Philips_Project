from fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn
import json

mcp = FastMCP("MonitoringAgent")
app = FastAPI()

# Load dataset
with open("vitals_patients.json", "r") as f:
    data = json.load(f)

# Pointer for time-series progression
index = 0

@mcp.tool()
def get_vitals():
    global index

    patient = data[index]
    index = (index + 1) % len(data)  # loop back after end

    return {
        "time": patient["time"],
        "patient_id": patient["patient_id"],
        "heart_rate": patient["heart_rate"],
        "spo2": patient["spo2"]
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
    uvicorn.run(app, port=9001)


