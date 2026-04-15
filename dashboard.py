import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import html as html_lib
from datetime import datetime
import random
from streamlit_autorefresh import st_autorefresh

# =========================================================================
# CONFIG & INIT
# =========================================================================
st.set_page_config(layout="wide", page_title="Philips HealthSuite", page_icon="⬡", initial_sidebar_state="expanded")

css_str = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
.stApp { background-color: #F8FAFC; font-family: 'Inter', sans-serif;}

/* Navbar */
.navbar { display: flex; justify-content: space-between; align-items: center; background: #FFFFFF; padding: 16px 32px; border-bottom: 1px solid #E2E8F0; margin: -60px -32px 40px -32px; box-shadow: 0 4px 12px rgba(0,0,0,0.02); }
.nav-brand { font-size: 26px; font-weight: 800; color: #0066A1; letter-spacing: -0.5px; display:flex; align-items:center; gap: 8px;}
.nav-brand span { color: #00B5E2; font-size: 32px; }

/* Triage Markers & Buttons (CSS Magic via :has() preventing any backend modification) */
div[data-testid="element-container"]:has(.marker-pat-active) + div[data-testid="element-container"] button {
    background-color: #0066A1 !important; color: #FFFFFF !important; border: 1px solid #005587 !important; font-weight: 700 !important; box-shadow: 0 4px 6px rgba(0, 102, 161, 0.3) !important;
}
div[data-testid="element-container"]:has(.marker-pat-inactive) + div[data-testid="element-container"] button {
    background-color: #F1F5F9 !important; color: #334155 !important; border: 1px solid #E2E8F0 !important; font-weight: 700 !important; transition: 0.2s !important;
}
div[data-testid="element-container"]:has(.marker-pat-inactive) + div[data-testid="element-container"] button:hover {
    background-color: #E0F2FE !important; border-color: #BAE6FD !important;
}

/* Emergency Soft Warning Buttons */
div[data-testid="element-container"]:has(.marker-cardiac) + div[data-testid="element-container"] button {
    background-color: #FEE2E2 !important; color: #1E293B !important; border: 1px solid #FCA5A5 !important; font-weight: 800 !important; transition: 0.2s !important; border-radius: 8px !important;
}
div[data-testid="element-container"]:has(.marker-cardiac) + div[data-testid="element-container"] button:hover { background-color: #FECACA !important; }

div[data-testid="element-container"]:has(.marker-hypoxia) + div[data-testid="element-container"] button {
    background-color: #E0F2FE !important; color: #1E293B !important; border: 1px solid #BAE6FD !important; font-weight: 800 !important; transition: 0.2s !important; border-radius: 8px !important;
}
div[data-testid="element-container"]:has(.marker-hypoxia) + div[data-testid="element-container"] button:hover { background-color: #BAE6FD !important; }

div[data-testid="element-container"]:has(.marker-sepsis) + div[data-testid="element-container"] button {
    background-color: #FFEDD5 !important; color: #1E293B !important; border: 1px solid #FDBA74 !important; font-weight: 800 !important; transition: 0.2s !important; border-radius: 8px !important;
}
div[data-testid="element-container"]:has(.marker-sepsis) + div[data-testid="element-container"] button:hover { background-color: #FDBA74 !important; }

div[data-testid="element-container"]:has(.marker-tachy) + div[data-testid="element-container"] button {
    background-color: #FEF9C3 !important; color: #1E293B !important; border: 1px solid #FDE047 !important; font-weight: 800 !important; transition: 0.2s !important; border-radius: 8px !important;
}
div[data-testid="element-container"]:has(.marker-tachy) + div[data-testid="element-container"] button:hover { background-color: #FEF08A !important; }


/* Timeline Cards */
.timeline-wrap { display: flex; flex-direction: column; gap: 16px; margin-bottom: 40px; }
.timeline-card { border-radius: 8px; background: #FFFFFF; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.04); border: 1px solid #E2E8F0; }
.t-normal { border-left: 6px solid #10B981; }
.t-medium { border-left: 6px solid #F59E0B; background: #FFFBEB; }
.t-high { border-left: 6px solid #F97316; background: #FFF7ED; }
.t-critical { border-left: 6px solid #EF4444; background: #FEF2F2; }
.t-header { font-weight: 800; font-size: 15px; margin-bottom: 12px; color: #1E293B; border-bottom: 1px solid rgba(0,0,0,0.05); padding-bottom: 12px; display: flex; justify-content: space-between; align-items: center;}
.t-row { font-size: 14px; font-weight: 600; color: #334155; padding: 6px 0; display: flex; align-items: center; gap: 8px; }

/* Visual Pipeline Stepper */
.pipeline-wrapper { background: #FFFFFF; border-radius: 12px; padding: 40px 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.04); margin-bottom: 40px; border: 1px solid #E2E8F0; transition: 0.4s; }
.pipeline-wrapper.critical-glow { border-color: #EF4444; box-shadow: 0 0 24px rgba(239, 68, 68, 0.2); }
.pipeline-status-text { font-size: 18px; font-weight: 800; color: #0066A1; margin-bottom: 40px; text-align: center; }
.pipeline-status-text.st-crit { color: #EF4444; animation: pulse-text-red 1.5s infinite; }
.stepper-container { display: flex; align-items: flex-start; justify-content: space-between; position: relative; padding: 0; }
.stepper-line { position: absolute; top: 32px; left: 8%; right: 8%; height: 6px; background: linear-gradient(90deg, #00B5E2, #0066A1); z-index: 1; border-radius: 3px; box-shadow: 0 0 10px rgba(0, 181, 226, 0.3);}
.step-item { display: flex; flex-direction: column; align-items: center; z-index: 2; width: 16%; text-align: center; }
.step-circle { width: 70px; height: 70px; border-radius: 50%; display: flex; justify-content: center; align-items: center; background: #FFFFFF; border: 4px solid #E2E8F0; font-size: 28px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 16px; transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.step-item.completed .step-circle { border-color: #10B981; background: #DCFCE7; color: #10B981; font-weight: 900; }
.step-item.pending .step-circle { background: #F1F5F9; opacity: 0.5; }
.step-item.active .step-circle { border-color: #00B5E2; background: #E0F2FE; transform: scale(1.15); box-shadow: 0 0 20px rgba(0, 181, 226, 0.5); animation: pulse-blue 1.5s infinite; color: #0066A1; font-weight: 900; }
.step-item.active.critical .step-circle { border-color: #EF4444; background: #FEE2E2; box-shadow: 0 0 24px rgba(239, 68, 68, 0.6); animation: pulse-red 1.2s infinite; color: #EF4444; font-weight: 900;}

@keyframes pulse-blue { 0% { box-shadow: 0 0 0 0 rgba(0,181,226,0.5); } 70% { box-shadow: 0 0 0 20px rgba(0,181,226,0); } 100% { box-shadow: 0 0 0 0 rgba(0,181,226,0); } }
@keyframes pulse-red { 0% { box-shadow: 0 0 0 0 rgba(239,68,68,0.6); } 70% { box-shadow: 0 0 0 24px rgba(239,68,68,0); } 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); } }
@keyframes pulse-text-red { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }

.step-title { font-weight: 800; font-size: 15px; color: #334155; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
.step-item.active .step-title { color: #0066A1; }
.step-item.active.critical .step-title { color: #EF4444; }
.step-desc { font-size: 13px; color: #64748B; line-height: 1.4; font-weight: 500; padding: 0 10px; }

/* Utils */
.section-title { font-size: 18px; font-weight: 800; color: #0066A1; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 24px; padding-top: 24px; }
.sticky-footer { position: fixed; bottom: 0; left: 0; width: 100%; background: #0066A1; color: #FFFFFF; text-align: center; padding: 14px; font-size: 13px; z-index: 1000; font-weight: 600; letter-spacing: 0.5px;}

/* Emergency Screen Flash Animation */
@keyframes emergencyFlash {
    0% { background-color: #FEE2E2; border-left: 10px solid #EF4444; box-shadow: inset 0 0 100px #EF4444; }
    100% { background-color: #F8FAFC; border-left: 5px solid #EF4444; box-shadow: inset 0 0 0px transparent; }
}

/* =========================================================
   Live System Terminal (UI-only, Philips theme preserved)
   ========================================================= */
.terminal-panel {
  background: #0F172A;
  color: #E2E8F0;
  border: 1px solid rgba(0, 181, 226, 0.25);
  border-radius: 10px;
  padding: 16px;
  height: 600px;
  overflow-y: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  box-shadow: 0 10px 30px rgba(2, 6, 23, 0.25);
  position: relative;
}
.terminal-header-title {
  font-weight: 900;
  letter-spacing: 0.2px;
  font-size: 16px;
  margin-bottom: 2px;
  color: #E2E8F0;
}
.terminal-header-subtitle {
  font-weight: 700;
  font-size: 12px;
  color: rgba(226, 232, 240, 0.72);
  margin-bottom: 12px;
}
.terminal-divider {
  height: 1px;
  background: linear-gradient(90deg, rgba(0,181,226,0.0), rgba(0,181,226,0.55), rgba(0,181,226,0.0));
  margin: 10px 0 12px 0;
}
.terminal-line {
  margin-bottom: 6px;
  font-size: 13px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-word;
  opacity: 0;
  transform: translateY(4px);
  animation: terminalFadeIn 220ms ease-out forwards;
}
@keyframes terminalFadeIn {
  to { opacity: 1; transform: translateY(0px); }
}
.terminal-ts {
  color: rgba(226, 232, 240, 0.55);
  margin-right: 8px;
}
.terminal-tag {
  font-weight: 900;
  letter-spacing: 0.4px;
  margin-right: 8px;
}
.terminal-tag.mcp { color: #38BDF8; }
.terminal-tag.a2a { color: #C084FC; }
.terminal-tag.crit { color: #F87171; text-shadow: 0 0 10px rgba(248, 113, 113, 0.18); }
.terminal-tag.ok { color: #4ADE80; }
.terminal-glow {
  box-shadow: 0 0 0 1px rgba(0,181,226,0.10) inset, 0 0 18px rgba(0,181,226,0.10);
  border-radius: 8px;
  padding: 8px 10px;
  background: rgba(2, 6, 23, 0.15);
}
.terminal-cursor {
  display: inline-block;
  width: 9px;
  height: 16px;
  background: rgba(226, 232, 240, 0.75);
  margin-left: 6px;
  border-radius: 2px;
  position: relative;
  top: 3px;
  animation: blink 1s step-end infinite;
}
@keyframes blink { 50% { opacity: 0; } }
</style>
"""
st.markdown(css_str.replace('\n', ' ').strip(), unsafe_allow_html=True)


# =========================================================================
# PRESENTATION CONTROLS (Sidebar & Refresh)
# =========================================================================
with st.sidebar:
    st.markdown("## ⚙️ Demo Controls")
    
    st.markdown("### ⏱️ Pipeline Engine")
    op_mode = st.radio("Simulation Speed", ["▶️ Auto Slow (5s)", "⏸️ Paused (Manual)"])
    force_next = st.button("⏭️ Next Force Step", width="stretch")

is_paused = "Paused" in op_mode
should_tick = False

if force_next:
    should_tick = True
elif not is_paused:
    refresh_counter = st_autorefresh(interval=5000, limit=10000, key="data_refresh_slow_v6")
    if 'last_refresh_counter' not in st.session_state: st.session_state.last_refresh_counter = refresh_counter
    if refresh_counter > st.session_state.last_refresh_counter:
        should_tick = True
        st.session_state.last_refresh_counter = refresh_counter


# =========================================================================
# STATE INITIALIZATION
# =========================================================================
patients_info = {
    "P-001": "Arjun Sharma", "P-002": "Meera Iyer", 
    "P-003": "David Osei", "P-004": "Fatima Al-Rashid"
}

if 'patients' not in st.session_state:
    st.session_state.patients = { pid: {"logs": [], "vhistory": [], "v": None, "a": None, "p": None, "sim_index": 0} for pid in patients_info }
if 'selected_patient' not in st.session_state: st.session_state.selected_patient = "P-001"

p_id = st.session_state.selected_patient
p_data = st.session_state.patients[p_id]
st.session_state.log_entries = p_data["logs"]
st.session_state.vitals_history = p_data["vhistory"]
st.session_state.sim_index = p_data["sim_index"]

# Emergency Trigger handling
if st.session_state.get('emergency_triggered_ui_flag'):
    st.markdown('<style>.stApp { animation: emergencyFlash 2.5s ease-out forwards; }</style>'.replace('\n', ' '), unsafe_allow_html=True)
    st.session_state.emergency_triggered_ui_flag = False

# Navbar Component
nav_html = '<div class="navbar"><div class="nav-brand"><span>⬡</span> Philips HealthSuite</div></div>'
st.markdown(nav_html, unsafe_allow_html=True)


# =========================================================================
# UI HELPERS (Rendering only — does not change engine/state)
# =========================================================================
def _terminal_escape(v):
    try:
        if isinstance(v, (dict, list)):
            return html_lib.escape(json.dumps(v, ensure_ascii=False))
        return html_lib.escape(str(v))
    except Exception:
        return html_lib.escape(repr(v))

def _infer_level(entry):
    # UI-only severity inference; relies on existing fields only.
    msg = str(entry.get("msg", ""))
    ev = str(entry.get("event_type", ""))
    css = str(entry.get("css", ""))
    if any(k in msg for k in ["CRITICAL", "ALERT", "ESCALATE"]) or "log-crit" in css:
        return "crit"
    if "Risk: NORMAL" in msg or "log-stable" in css:
        return "ok"
    if entry.get("proto") == "A2A":
        return "a2a"
    return "mcp"


def _extract_tool_name(text):
    t = (text or "").strip()
    if "(" in t:
        return t.split("(", 1)[0].strip()
    return t.split()[0].strip() if t else ""


def _format_terminal_lines(log_entries):
    lines = []

    for e in (log_entries or []):
        ts = e.get("ts", "")
        proto = e.get("proto", "")
        ev = e.get("event_type", "")
        frm = e.get("frm", "")
        to = e.get("to", "")
        msg = e.get("msg", "")

        level = _infer_level(e)
        tag_cls = "crit" if level == "crit" else ("a2a" if proto == "A2A" else ("ok" if level == "ok" else "mcp"))

        # =========================
        # MCP FORMATTING
        # =========================
        if proto == "MCP":

            # --- VITALS ---
            if ev == "TOOL_RESULT" and ("HR:" in str(msg) and "SpO2:" in str(msg)):
                hr = None
                sp = None
                try:
                    parts = str(msg).replace(",", " ").split()
                    if "HR:" in parts:
                        hr = int(parts[parts.index("HR:") + 1])
                    if "SpO2:" in parts:
                        sp = int(parts[parts.index("SpO2:") + 1])
                except:
                    pass

                vitals_obj = {"heart_rate": hr, "spo2": sp}

                lines.append({
                    "ts": ts,
                    "tag": "[VITALS]",
                    "tag_cls": "mcp",
                    "text": _terminal_escape(vitals_obj),
                    "level": level
                })
                continue

            # --- PLANNER OUTPUT → MCP TOOL CALLED ---
            if ev in ["LLM_RESULT", "LLM_PLAN"]:
                plan_txt = str(msg).replace("Plan:", "").strip()
                tools = plan_txt.replace("[", "").replace("]", "").split("→")

                for t in tools:
                    t = t.strip()
                    if t:
                        lines.append({
                            "ts": ts,
                            "tag": "[MCP]",
                            "tag_cls": "mcp",
                            "text": _terminal_escape(f"MCP TOOL CALLED: {t}"),
                            "level": level
                        })
                continue

            # --- TOOL EXECUTION ---
            if ev in ["TOOL_CALL", "TOOL_RESULT"]:
                tool = _extract_tool_name(str(msg))

                if ev == "TOOL_CALL":
                    lines.append({
                        "ts": ts,
                        "tag": "[MCP]",
                        "tag_cls": "mcp",
                        "text": _terminal_escape(f"main.py executing {tool}"),
                        "level": level
                    })
                else:
                    lines.append({
                        "ts": ts,
                        "tag": "[MCP]",
                        "tag_cls": "crit" if level == "crit" else "mcp",
                        "text": _terminal_escape(f"{tool} result → {msg}"),
                        "level": level
                    })
                continue

            # --- FALLBACK MCP ---
            lines.append({
                "ts": ts,
                "tag": "[MCP]",
                "tag_cls": "mcp",
                "text": _terminal_escape(f"{frm} → {to} | {ev} | {msg}"),
                "level": level
            })
            continue

        # =========================
        # A2A FORMATTING
        # =========================
        if proto == "A2A":

            # --- BROADCAST ---
            if ev == "BROADCAST":
                lines.append({
                    "ts": ts,
                    "tag": "[A2A]",
                    "tag_cls": "crit" if level == "crit" else "a2a",
                    "text": _terminal_escape("main.py sending A2A message via A2A_bus"),
                    "level": level
                })
                lines.append({
                    "ts": "",
                    "tag": "",
                    "tag_cls": "a2a",
                    "text": _terminal_escape(f"{frm} → A2A_bus → {to} | {msg}"),
                    "level": level
                })
                continue

            # --- DOCTOR ---
            if ev == "DELIVER" and str(to).lower() == "doctor":
                lines.append({"ts": ts, "tag": "[DOCTOR_AGENT]", "tag_cls": "a2a", "text": "", "level": level})
                lines.append({"ts": "", "tag": "", "tag_cls": "a2a", "text": _terminal_escape(f"From: {frm}"), "level": level})
                lines.append({"ts": "", "tag": "", "tag_cls": "a2a", "text": _terminal_escape(f"Type: {ev}"), "level": level})
                lines.append({"ts": "", "tag": "", "tag_cls": "a2a", "text": _terminal_escape(f"Payload: {msg}"), "level": level})
                continue

            # --- CAREGIVER ---
            if ev == "DELIVER" and str(to).lower() == "caregiver":
                lines.append({"ts": ts, "tag": "[CAREGIVER_AGENT]", "tag_cls": "a2a", "text": "", "level": level})
                lines.append({"ts": "", "tag": "", "tag_cls": "a2a", "text": _terminal_escape(f"From: {frm}"), "level": level})
                lines.append({"ts": "", "tag": "", "tag_cls": "a2a", "text": _terminal_escape(f"Type: {ev}"), "level": level})
                lines.append({"ts": "", "tag": "", "tag_cls": "a2a", "text": _terminal_escape(f"Payload: {msg}"), "level": level})
                lines.append({"ts": "", "tag": "", "tag_cls": "ok", "text": _terminal_escape("[Caregiver Action] Executing care instruction..."), "level": "ok"})
                continue

            # --- GENERIC RECEIVED ---
            if ev == "RECEIVED":
                who = f"{frm.upper()}_AGENT" if frm else "AGENT"
                lines.append({
                    "ts": ts,
                    "tag": "[A2A]",
                    "tag_cls": "a2a",
                    "text": _terminal_escape(f"{who}: {msg}"),
                    "level": level
                })
                continue

            # --- FALLBACK A2A ---
            lines.append({
                "ts": ts,
                "tag": "[A2A]",
                "tag_cls": "a2a",
                "text": _terminal_escape(f"{frm} → A2A_bus → {to} | {ev} | {msg}"),
                "level": level
            })
            continue

        # =========================
        # FALLBACK
        # =========================
        lines.append({
            "ts": ts,
            "tag": "[LOG]",
            "tag_cls": tag_cls,
            "text": _terminal_escape(f"{proto} | {ev} | {msg}"),
            "level": level
        })

    return lines


def render_live_terminal():
    # Uses ONLY st.session_state.log_entries; UI rendering only.
    log_entries = st.session_state.get("log_entries", [])
    lines = _format_terminal_lines(log_entries)

    header = """
      <div class="terminal-header-title">🖥️ Live Agent Communication</div>
      <div class="terminal-header-subtitle">Real-time MCP + Gemini + A2A Logs</div>
      <div class="terminal-divider"></div>
    """

    if not lines:
        body = '<div class="terminal-line terminal-glow"><span class="terminal-tag mcp">[WAITING]</span> <span style="color: rgba(226,232,240,0.75);">No logs yet — waiting for pipeline ticks…</span><span class="terminal-cursor"></span></div>'
    else:
        rendered = []
        for i, ln in enumerate(lines[-120:]):
            is_active = (i >= max(0, len(lines[-120:]) - 10))
            glow = " terminal-glow" if is_active else ""
            ts_html = f'<span class="terminal-ts">{_terminal_escape(ln.get("ts",""))}</span>' if ln.get("ts") else '<span class="terminal-ts"></span>'
            tag = ln.get("tag", "")
            tag_html = f'<span class="terminal-tag {ln.get("tag_cls","mcp")}">{_terminal_escape(tag)}</span>' if tag else '<span class="terminal-tag"></span>'
            text_html = f'<span>{ln.get("text","")}</span>' if ln.get("text") else ""
            rendered.append(f'<div class="terminal-line{glow}">{ts_html}{tag_html}{text_html}</div>')
        rendered.append('<div class="terminal-line"><span class="terminal-tag mcp">[READY]</span> <span style="color: rgba(226,232,240,0.75);">Listening…</span><span class="terminal-cursor"></span></div>')
        body = "".join(rendered)

    # Auto-scroll to bottom (smooth), UI-only.
    script = """
    <script>
      const el = document.getElementById("live-terminal-scroll");
      if (el) { el.scrollTo({ top: el.scrollHeight, behavior: "smooth" }); }
    </script>
    """

    html = f'<div id="live-terminal-scroll" class="terminal-panel">{header}{body}</div>{script}'
    st.markdown(html.replace("\n", " ").strip(), unsafe_allow_html=True)


# =========================================================================
# AGENT STATUS (CORE PRESERVED)
# =========================================================================
def check_agent(port, path=""):
    try: return requests.get(f"http://127.0.0.1:{port}/{path}".rstrip("/"), timeout=0.5).status_code == 200
    except: return False

agents = [{"port": 9001, "path": "mcp/tools"}, {"port": 9002, "path": "mcp/tools"}, {"port": 9003, "path": "mcp/tools"}, {"port": 8000, "path": "health"}]
live_mode = all(check_agent(a['port'], a['path']) for a in agents)

# =========================================================================
# PATIENT SELECTOR TAB BAR
# =========================================================================
# MAIN LAYOUT SPLIT (Left: existing dashboard; Right: live terminal)
main_left = st.container()
main_right = st.container()

with main_left:
    st.markdown('<div class="section-title" style="padding-top: 0;">Patient Triage Area</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for i, (pid, pname) in enumerate(patients_info.items()):
        p_state = st.session_state.patients[pid]
        risk = "NORMAL"
        if p_state["a"] and "risk" in p_state["a"]: risk = p_state["a"]["risk"]
        dot = "🟢"
        if risk == "CRITICAL": dot = "🔴"
        elif risk == "HIGH": dot = "🟠"
        elif risk == "MEDIUM": dot = "🟡"
        
        with cols[i]:
            # Emits empty invisible marker allowing CSS to precisely style the NEXT element dynamically!
            marker = "marker-pat-active" if pid == p_id else "marker-pat-inactive"
            st.markdown(f'<div class="{marker}"></div>', unsafe_allow_html=True)
            if st.button(f"{dot} {pid} — {pname}", key=f"sel_{pid}", width="stretch"):
                st.session_state.selected_patient = pid
                st.rerun()

    # =========================================================================
    # RED EMERGENCY PANEL
    # =========================================================================
    st.markdown('<div class="section-title" style="margin-top: 32px; color: #334155;">🚨 SIMULATE EMERGENCY SCENARIO</div>', unsafe_allow_html=True)
    ecol1, ecol2, ecol3, ecol4 = st.columns(4)

    with ecol1:
        st.markdown('<div class="marker-cardiac"></div>', unsafe_allow_html=True)
        if st.button("CARDIAC ARREST", width="stretch"): st.session_state.emergency_inject, st.session_state.emergency_triggered_ui_flag = "CARDIAC", True
    with ecol2:
        st.markdown('<div class="marker-hypoxia"></div>', unsafe_allow_html=True)
        if st.button("HYPOXIA", width="stretch"): st.session_state.emergency_inject, st.session_state.emergency_triggered_ui_flag = "HYPOXIA", True
    with ecol3:
        st.markdown('<div class="marker-sepsis"></div>', unsafe_allow_html=True)
        if st.button("SEPSIS ALERT", width="stretch"): st.session_state.emergency_inject, st.session_state.emergency_triggered_ui_flag = "SEPSIS", True
    with ecol4:
        st.markdown('<div class="marker-tachy"></div>', unsafe_allow_html=True)
        if st.button("TACHYCARDIA", width="stretch"): st.session_state.emergency_inject, st.session_state.emergency_triggered_ui_flag = "TACHY", True


# =========================================================================
# CORE GENERATION LOGIC (UNCHANGED)
# =========================================================================
def get_event_color(ev): pass
def add_log(proto, frm, to, ev, msg, css="log-mcp"):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_entries.append({"ts": ts, "proto": proto, "frm": frm, "to": to, "event_type": ev, "msg": msg, "css": css})

def resolve_sim_rules(v):
    hr, spo2 = v["heart_rate"], v["spo2"]
    if spo2 < 85 or hr > 140: return {"risk": "CRITICAL", "reason": "Heart rate extremely high or SpO2 critically low."}, {"action": "CRITICAL", "plan": "ICU Escalation. Immediate code team dispatch.", "source": "LLM+RULES"}
    elif hr > 120 or spo2 < 90: return {"risk": "HIGH", "reason": "Signs of severe physiological distress."}, {"action": "ALERT", "plan": "Notify resident on call for immediate review.", "source": "LLM+RULES"}
    elif hr > 100 or spo2 < 94: return {"risk": "MEDIUM", "reason": "Elevated heart rate and reduced oxygenation."}, {"action": "ESCALATE", "plan": "Increase monitoring frequency to every 15 minutes.", "source": "LLM+RULES"}
    else: return {"risk": "NORMAL", "reason": "Vitals are within physiological limits."}, {"action": "MONITOR", "plan": "Continue standard monitoring.", "source": "LLM+RULES"}

def process_cycle(v, a, p):
    hr, spo2 = v.get('heart_rate',0), v.get('spo2',0)
    risk, reason = a.get('risk','NORMAL'), a.get('reason','')
    action, planStr = p.get('action','MONITOR'), p.get('plan','')
    add_log("MCP", "Orchestrator", "MonitoringAgent", "TOOL_CALL", "get_vitals() invoked", "log-mcp")
    add_log("MCP", "MonitoringAgent", "Orchestrator", "TOOL_RESULT", f"HR: {hr}, SpO2: {spo2}", "log-mcp")
    add_log("MCP", "Orchestrator", "Gemini Planner", "LLM_PLAN", "Planning tool sequence...", "log-mcp")
    add_log("MCP", "Gemini Planner", "Orchestrator", "LLM_RESULT", "Plan: [analyze_vitals → plan]", "log-mcp")
    add_log("MCP", "Orchestrator", "AnalysisAgent", "TOOL_CALL", f"analyze_vitals({hr}, {spo2})", "log-mcp")
    css1 = "log-crit" if risk in ["CRITICAL","HIGH"] else ("log-stable" if risk=="NORMAL" else "log-mcp")
    add_log("MCP", "AnalysisAgent", "Orchestrator", "TOOL_RESULT", f"Risk: {risk} — {reason}", css1)
    add_log("MCP", "Orchestrator", "CarePlanAgent", "TOOL_CALL", f"plan(vitals, analysis)", "log-mcp")
    css2 = "log-crit" if action in ["ALERT", "ESCALATE", "CRITICAL"] else "log-stable"
    add_log("MCP", "CarePlanAgent", "Orchestrator", "TOOL_RESULT", f"Action: {action} — {planStr}", css2)
    if action in ["ALERT", "ESCALATE", "CRITICAL"]:
        add_log("A2A", "ChiefResident", "Bus", "BROADCAST", f"Sending {action} to all subscribers", "log-crit")
        add_log("A2A", "Bus", "Doctor", "DELIVER", f"Alert delivered: {action}", "log-a2a")
        add_log("A2A", "Bus", "Caregiver", "DELIVER", f"Action delivered: {action}", "log-a2a")
        add_log("A2A", "Doctor", "(log)", "RECEIVED", "Doctor notified — reviewing patient", "log-a2a")
        add_log("A2A", "Caregiver", "(log)", "RECEIVED", f"Caregiver executing: {planStr}", "log-a2a")

def get_realistic_vitals(p_id, sim_idx):
    base_hr = {"P-001": 75, "P-002": 115, "P-003": 70, "P-004": 85}[p_id]
    base_sp = {"P-001": 98, "P-002": 92, "P-003": 98, "P-004": 96}[p_id]
    
    cycle_pos = sim_idx % 10
    spike_mult_hr = 0
    spike_mult_sp = 0
    
    if cycle_pos == 4:
        spike_mult_hr = 10; spike_mult_sp = -2
    elif cycle_pos in [5, 6]:
        spike_mult_hr = 30; spike_mult_sp = -6
    elif cycle_pos == 7:
        spike_mult_hr = 15; spike_mult_sp = -3
    elif cycle_pos in [8, 9]:
        spike_mult_hr = 5; spike_mult_sp = -1

    if p_id == "P-001":
        base_hr += (sim_idx * 1.5)
        base_sp -= (sim_idx * 0.3)
    elif p_id == "P-003":
        spike_mult_hr = 0; spike_mult_sp = 0

    hr = int(base_hr + spike_mult_hr + random.randint(-2, 2))
    spo2 = int(base_sp + spike_mult_sp + random.randint(-1, 1))
    return {"time": sim_idx, "patient_id": p_id, "heart_rate": max(40, min(190, hr)), "spo2": max(60, min(100, spo2))}


# Execute Engine
if should_tick or st.session_state.get('emergency_inject'):
    v, a, p = None, None, None
    em = st.session_state.get('emergency_inject')
    
    if em:
        if em == "CARDIAC":
            v = {"time": int(datetime.now().timestamp()%1000), "patient_id": p_id, "heart_rate": 0, "spo2": 60}
            a = {"risk": "CRITICAL", "reason": "No cardiac output detected"}
            p = {"action": "CRITICAL", "plan": "Immediate code team dispatch. Begin CPR.", "source": "OVERRIDE"}
        elif em == "HYPOXIA":
            v = {"time": int(datetime.now().timestamp()%1000), "patient_id": p_id, "heart_rate": 130, "spo2": 72}
            a = {"risk": "CRITICAL", "reason": "Critical oxygen desaturation"}
            p = {"action": "CRITICAL", "plan": "Apply high-flow oxygen. Intubation prep.", "source": "OVERRIDE"}
        elif em == "SEPSIS":
            v = {"time": int(datetime.now().timestamp()%1000), "patient_id": p_id, "heart_rate": 145, "spo2": 88}
            a = {"risk": "HIGH", "reason": "Sepsis protocol initiated"}
            p = {"action": "ALERT", "plan": "Administer broad-spectrum antibiotics and fluids.", "source": "OVERRIDE"}
        elif em == "TACHY":
            v = {"time": int(datetime.now().timestamp()%1000), "patient_id": p_id, "heart_rate": 178, "spo2": 94}
            a = {"risk": "CRITICAL", "reason": "Ventricular tachycardia risk"}
            p = {"action": "CRITICAL", "plan": "Prepare defibrillator. Amiodarone administration.", "source": "OVERRIDE"}
        st.session_state.emergency_inject = None
        
    elif live_mode:
        try:
            v = requests.post("http://127.0.0.1:9001/tools/get_vitals", timeout=1).json()
            a = requests.post("http://127.0.0.1:9002/tools/analyze_vitals", json={"heart_rate": v["heart_rate"], "spo2": v["spo2"]}, timeout=1).json()
            p = requests.post("http://127.0.0.1:9003/tools/plan", json={"vitals": v, "analysis": a}, timeout=1).json()
        except:
            v = get_realistic_vitals(p_id, st.session_state.sim_index)
            a, p = resolve_sim_rules(v)
    else:
        v = get_realistic_vitals(p_id, st.session_state.sim_index)
        a, p = resolve_sim_rules(v)
        st.session_state.sim_index += 1

    if v and a and p:
        process_cycle(v, a, p)
        p_data["v"], p_data["a"], p_data["p"] = v, a, p
        st.session_state.vitals_history.append(v)
        if force_next: st.rerun()

# Memory Truncation
if len(st.session_state.vitals_history) > 60: st.session_state.vitals_history = st.session_state.vitals_history[-60:]
if len(st.session_state.log_entries) > 60: st.session_state.log_entries = st.session_state.log_entries[-60:]
p_data["logs"], p_data["vhistory"], p_data["sim_index"] = st.session_state.log_entries, st.session_state.vitals_history, st.session_state.sim_index
v, a, p = p_data["v"], p_data["a"], p_data["p"]


# =========================================================================
# EXPERT VISUAL STEPPER PIPELINE
# =========================================================================
with main_right:
    render_live_terminal()

with main_left:
    active_index = 0
    is_crit = False

    if p:
        is_crit = p['action'] in ["CRITICAL"]
        if p['action'] in ["ALERT", "ESCALATE", "CRITICAL"]:
            active_index = 5
        else:
            active_index = 3

    status_msg = "🔄 Waiting for datastream via clinical network..."
    if active_index == 3: status_msg = "✅ Pipeline complete — Standard clinical monitoring continues"
    elif active_index == 5: status_msg = "🚨 DISPATCHING CRITICAL ALERTS TO CLINICAL TEAM" if is_crit else "🔄 Currently: Routing alerts via A2A framework"

    steps_data = [
        {"icon": "🩺", "title": "Monitoring", "desc": "Capturing patient vitals"},
        {"icon": "🤖", "title": "AI Planning", "desc": "Mapping analysis sequence"},
        {"icon": "📊", "title": "Analysis", "desc": "Evaluating risk levels"},
        {"icon": "📋", "title": "Care Plan", "desc": "Formulating protocol"},
        {"icon": "📡", "title": "Dispatch", "desc": "Routing alerts via A2A"},
        {"icon": "👨‍⚕️", "title": "Clinical Team", "desc": "Doctor/Caregiver notified"}
    ]

    wrapper_class = "critical-glow" if (is_crit and active_index == 5) else ""
    crit_status_class = "st-crit" if (is_crit and active_index == 5) else ""

    stepper_html = f'<div class="pipeline-wrapper {wrapper_class}">'
    stepper_html += f'<div class="pipeline-status-text {crit_status_class}">{"🔄" if active_index < 5 and not is_crit else ""} {status_msg}</div>'
    stepper_html += '<div class="stepper-container"><div class="stepper-line"></div>'
    for i, step in enumerate(steps_data):
        state = "pending"
        circle_html = f'{step["icon"]}'
        
        if i < active_index:
            state = "completed"
            circle_html = "✔️"
        elif i == active_index:
            state = "active"
            if is_crit and i == 5: state += " critical"
            
        stepper_html += f'<div class="step-item {state}"><div class="step-circle">{circle_html}</div><div class="step-title">{step["title"]}</div><div class="step-desc">{step["desc"]}</div></div>'

    stepper_html += '</div></div>'
    st.markdown(stepper_html.replace('\n', ' ').strip(), unsafe_allow_html=True)


with main_left:
    # =========================================================================
    # UI RENDERING: STATUS CARD & VITALS CHART
    # =========================================================================
    col_left, col_right = st.columns([35, 65])

    with col_left:
        st.markdown('<div class="section-title">Patient Status</div>', unsafe_allow_html=True)
        if v and a and p:
            rc = {"CRITICAL": "#DC2626", "HIGH": "#EA580C", "MEDIUM": "#CA8A04", "NORMAL": "#16A34A"}.get(a['risk'])
            hr_c = "#DC2626" if v['heart_rate']>120 else "#16A34A"
            sp_c = "#DC2626" if v['spo2']<90 else "#16A34A"
            ai_rsn = a['reason']
            rec_act = p['plan']

            status_html = f'<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden; height: 100%; box-shadow: 0 4px 12px rgba(0,0,0,0.04); margin-bottom: 40px;">'
            status_html += f'<div style="background:{rc}; color:white; padding:16px; text-align:center; font-size:22px; font-weight:800; letter-spacing:1px; text-transform:uppercase;">{a["risk"]} — {p["action"]}</div>'
            status_html += '<div style="padding:32px;">'
            status_html += '<div style="display:flex; justify-content:space-around; margin-bottom: 40px;">'
            status_html += f'<div style="text-align:center;"><div style="font-weight:800; color:#0066A1; font-size:16px; margin-bottom: 12px; text-transform:uppercase;">❤️ Heart Rate</div><div style="font-size:56px; font-weight:900; color:#1E293B; line-height:1;">{v["heart_rate"]}<span style="font-size:20px; font-weight:800;"> bpm</span></div><div style="color:{hr_c}; font-weight:800; font-size:15px; margin-top: 10px;">{"⚠️ Elevated" if v["heart_rate"]>120 else "✅ Normal"}</div></div>'
            status_html += f'<div style="text-align:center;"><div style="font-weight:800; color:#0066A1; font-size:16px; margin-bottom: 12px; text-transform:uppercase;">🫁 Blood Oxygen</div><div style="font-size:56px; font-weight:900; color:#1E293B; line-height:1;">{v["spo2"]}<span style="font-size:20px; font-weight:800;"> %</span></div><div style="color:{sp_c}; font-weight:800; font-size:15px; margin-top: 10px;">{"⚠️ Depleted" if v["spo2"]<90 else "✅ Safe"}</div></div>'
            status_html += '</div>'
            status_html += f'<div style="background:#F8FAFC; padding:20px; border-left:5px solid #00B5E2; border-radius:6px; margin-bottom: 20px;"><div style="font-weight:800; font-size:13px; color:#0066A1; text-transform:uppercase; margin-bottom:6px;">💡 AI Clinical Reasoning</div><div style="font-weight:600; color:#334155; font-size:16px;">{ai_rsn}</div></div>'
            status_html += f'<div style="background:#F8FAFC; padding:20px; border-left:5px solid #0066A1; border-radius:6px;"><div style="font-weight:800; font-size:13px; color:#0066A1; text-transform:uppercase; margin-bottom:6px;">🎯 Recommended Action</div><div style="font-weight:800; color:#1E293B; font-size:18px;">{rec_act}</div></div>'
            status_html += '</div></div>'
            
            st.markdown(status_html.replace('\n', ' ').strip(), unsafe_allow_html=True)
        else:
            st.info("Waiting for patient data stream...")

    with col_right:
        st.markdown(f'<div class="section-title">Vitals Stream — {patients_info[p_id]}</div>', unsafe_allow_html=True)
        vh = p_data["vhistory"]
        if len(vh) > 0:
            df = pd.DataFrame(vh[-15:])
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            danger_hr = df[df['heart_rate'] > 120]
            danger_sp = df[df['spo2'] < 90]
            
            fig.add_trace(go.Scatter(x=df['time'].astype(str), y=df['heart_rate'], mode='lines', name='HR', line=dict(color='#0066A1', width=3)), secondary_y=False)
            if not danger_hr.empty: fig.add_trace(go.Scatter(x=danger_hr['time'].astype(str), y=danger_hr['heart_rate'], mode='markers', name='HR Danger', marker=dict(color='red', size=12)), secondary_y=False)
            
            fig.add_trace(go.Scatter(x=df['time'].astype(str), y=df['spo2'], mode='lines', name='SpO2', line=dict(color='#00B5E2', width=3)), secondary_y=True)
            if not danger_sp.empty: fig.add_trace(go.Scatter(x=danger_sp['time'].astype(str), y=danger_sp['spo2'], mode='markers', name='SpO2 Danger', marker=dict(color='red', size=12)), secondary_y=True)
            
            fig.add_hrect(y0=60, y1=100, fillcolor="#16A34A", opacity=0.08, secondary_y=False)
            fig.add_hrect(y0=100, y1=120, fillcolor="#CA8A04", opacity=0.08, secondary_y=False)
            fig.add_hrect(y0=120, y1=200, fillcolor="#DC2626", opacity=0.08, secondary_y=False)
            fig.add_hline(y=120, line_dash="dash", line_color="#DC2626", secondary_y=False)
            
            fig.add_hrect(y0=95, y1=100, fillcolor="#16A34A", opacity=0.08, secondary_y=True)
            fig.add_hrect(y0=90, y1=94, fillcolor="#CA8A04", opacity=0.08, secondary_y=True)
            fig.add_hrect(y0=40, y1=89, fillcolor="#DC2626", opacity=0.08, secondary_y=True)
            fig.add_hline(y=90, line_dash="dash", line_color="#DC2626", secondary_y=True)
            
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", margin=dict(l=0, r=0, t=20, b=0), showlegend=False, height=520, hovermode="x unified")
            fig.update_yaxes(title_text="Heart Rate (bpm)", secondary_y=False, range=[40, 200], title_font=dict(size=14, weight="bold"))
            fig.update_yaxes(title_text="SpO2 (%)", secondary_y=True, range=[60, 100], title_font=dict(size=14, weight="bold"))
            st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})
        else:
            st.info("No telemetry data yet.")


    # =========================================================================
    # CLINICAL EVENT TIMELINE
    # =========================================================================
    st.markdown('<div class="section-title">Clinical Event Timeline</div>', unsafe_allow_html=True)

    def extract_cycles():
        logs = st.session_state.log_entries
        cycles, curr = [], []
        for l in logs:
            if "get_vitals" in l["msg"] and curr:
                cycles.append(curr)
                curr = []
            curr.append(l)
        if curr: cycles.append(curr)
        return cycles[::-1]

    cycles = extract_cycles()

    timeline_html = '<div class="timeline-wrap">'
    for idx, cyc in enumerate(cycles[:10]):
        t_start = cyc[0]['ts']
        risk = "NORMAL"
        for l in cyc:
            if "Risk:" in l["msg"]: risk = l["msg"].split("—")[0].replace("Risk:","").strip()
        
        rc_class = {"CRITICAL": "t-critical", "HIGH": "t-high", "MEDIUM": "t-medium", "NORMAL": "t-normal"}.get(risk, "t-normal")
        emoji = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "🟡", "NORMAL": "🟢"}.get(risk, "🟢")

        card_html = f'<div class="timeline-card {rc_class}"><div class="t-header"><span><b>CYCLE #{len(cycles)-idx}</b> &nbsp;|&nbsp; {emoji} {risk} RISK</span><span>{t_start}</span></div>'
        
        step_vitals, step_ai, step_care, step_alert = False, False, False, False
        for l in cyc:
            msg, ev = l['msg'], l['event_type']
            if "HR:" in msg: step_vitals = True
            if "Risk:" in msg: step_ai = True
            if "Action:" in msg: step_care = True
            if "DELIVER" in ev or "BROADCAST" in ev: step_alert = True
            
        card_html += f'<div class="t-row">{"✔️" if step_vitals else "⚪"} 🩺 Capturing vitals via patient monitoring suite</div>'
        card_html += f'<div class="t-row">{"✔️" if step_ai else "⚪"} 📊 Executing AI clinical analysis protocol</div>'
        card_html += f'<div class="t-row">{"✔️" if step_care else "⚪"} 💊 Resolving target care pathway and decision logic</div>'
        card_html += f'<div class="t-row">{"✔️" if step_alert else "⚪"} 📡 Alert framework engaged via A2A distribution</div>'
        card_html += '</div>'
        timeline_html += card_html
    timeline_html += '</div>'

    st.markdown(timeline_html.replace('\n', ' ').strip(), unsafe_allow_html=True)
    st.markdown('<div class="sticky-footer">Philips HealthSuite Agent Platform | Clinical Decision Support Only | Not for autonomous treatment</div>', unsafe_allow_html=True)
