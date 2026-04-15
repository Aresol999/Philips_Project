import net_bootstrap  # noqa: F401 (ensure SSLKEYLOGFILE disabled early)

import subprocess
import sys
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run(file):
    return subprocess.Popen([sys.executable, file])

# Start A2A Bus FIRST
bus = run("a2a_bus.py")
print("Started A2A Bus...")
time.sleep(3)

# Start MCP Agents
monitor = run("monitoring_agent.py")
analysis = run("analysis_agent.py")
care = run("careplan_agent.py")
print("Started MCP agents...")
time.sleep(3)

# Start A2A Agents
doctor = run("doctor_agent.py")
caregiver = run("caregiver_agent.py")
print("Started A2A agents...")
time.sleep(3)

# Start Orchestrator
main = run("main.py")
print("Started orchestrator...")
time.sleep(2)

# Start Dashboard

subprocess.Popen([
    "streamlit", "run",
    os.path.join(BASE_DIR, "dashboard.py")
])

#subprocess.Popen([sys.executable, "-m", "streamlit", "run", "dashboard.py"])

# Keep running
bus.wait()
