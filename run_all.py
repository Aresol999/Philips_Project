import subprocess
import sys
import time
import os
import signal

processes = []

def run(file):
    p = subprocess.Popen([sys.executable, file])
    processes.append(p)
    return p

try:
    run("a2a_bus.py")
    time.sleep(2)

    run("monitoring_agent.py")
    run("analysis_agent.py")
    run("careplan_agent.py")
    time.sleep(2)

    run("doctor_agent.py")
    run("caregiver_agent.py")
    time.sleep(2)

    run("main.py")
    time.sleep(2)

    subprocess.Popen([
        "streamlit", "run",
        os.path.join(os.getcwd(), "dashboard.py")
    ])

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nShutting down all services...")

    for p in processes:
        try:
            p.terminate()
        except:
            pass

    for p in processes:
        try:
            p.wait(timeout=5)
        except:
            p.kill()

    print("All processes stopped.")
